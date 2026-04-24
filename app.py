import os, time, json, random, socket, threading, asyncio, hashlib, base64
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import hmac
import uuid
import struct

# ================== ENCRYPTION/DECRYPTION HELPERS ==================
def aes_encrypt(data, key, iv):
    """AES CBC encryption with PKCS7 padding"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def aes_decrypt(data, key, iv):
    """AES CBC decryption with PKCS7 padding"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data), AES.block_size)

def generate_auth_token(uid, password, timestamp):
    """Generate HMAC-based auth token"""
    secret = hashlib.sha256(f"{uid}:{password}:EREN_CORE_SECRET".encode()).digest()
    message = f"{uid}:{timestamp}".encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return f"{uid}.{timestamp}.{signature}"

# ================== PROTOBUF-LIKE ENCODING ==================
class ProtoEncoder:
    """Custom protobuf-like field encoder"""
    
    @staticmethod
    def encode_varint(value):
        """Encode integer as varint"""
        result = []
        while True:
            byte = value & 0x7F
            value >>= 7
            if value:
                byte |= 0x80
            result.append(byte)
            if not value:
                break
        return bytes(result)
    
    @staticmethod
    def decode_varint(data, offset=0):
        """Decode varint from bytes"""
        result = 0
        shift = 0
        while True:
            byte = data[offset]
            result |= (byte & 0x7F) << shift
            offset += 1
            shift += 7
            if not (byte & 0x80):
                break
        return result, offset
    
    @staticmethod
    def encode_field(field_number, wire_type, value_bytes):
        """Encode a single field (tag + length + value)"""
        tag = (field_number << 3) | wire_type
        tag_bytes = ProtoEncoder.encode_varint(tag)
        
        if wire_type == 0:  # Varint
            return tag_bytes + value_bytes
        elif wire_type == 2:  # Length-delimited
            length_bytes = ProtoEncoder.encode_varint(len(value_bytes))
            return tag_bytes + length_bytes + value_bytes
        
    @staticmethod
    def create_varint_field(field_number, value):
        """Create varint field"""
        return ProtoEncoder.encode_field(field_number, 0, ProtoEncoder.encode_varint(value))
    
    @staticmethod
    def create_bytes_field(field_number, value):
        """Create length-delimited field"""
        if isinstance(value, str):
            value = value.encode('utf-8')
        return ProtoEncoder.encode_field(field_number, 2, value)
    
    @staticmethod
    def create_message_field(field_number, message_bytes):
        """Create nested message field"""
        return ProtoEncoder.create_bytes_field(field_number, message_bytes)

# ================== PACKET BUILDERS ==================
def build_spam_packet(target_uid, room_id=1):
    """Build spam message packet"""
    packet = bytearray()
    
    # Field 1: Message type (22 = spam)
    packet.extend(ProtoEncoder.create_varint_field(1, 22))
    
    # Field 2: Spam data (nested message)
    spam_data = bytearray()
    spam_data.extend(ProtoEncoder.create_varint_field(1, int(target_uid)))
    spam_data.extend(ProtoEncoder.create_varint_field(2, room_id))
    spam_data.extend(ProtoEncoder.create_varint_field(3, 999))  # Spam count
    
    packet.extend(ProtoEncoder.create_message_field(2, bytes(spam_data)))
    
    return bytes(packet)

def build_join_room_packet(room_id=1):
    """Build room join packet"""
    packet = bytearray()
    
    # Field 1: Message type (2 = join room)
    packet.extend(ProtoEncoder.create_varint_field(1, 2))
    
    # Field 2: Room data (nested message)
    room_data = bytearray()
    room_data.extend(ProtoEncoder.create_varint_field(1, 1))  # Action: join
    room_data.extend(ProtoEncoder.create_varint_field(2, 15))  # Protocol version
    room_data.extend(ProtoEncoder.create_varint_field(3, 5))   # Room type
    room_data.extend(ProtoEncoder.create_bytes_field(4, "EREN_CORE"))  # Room name
    room_data.extend(ProtoEncoder.create_bytes_field(5, "1"))  # Version
    room_data.extend(ProtoEncoder.create_varint_field(6, 12))  # Max users
    room_data.extend(ProtoEncoder.create_varint_field(7, 1))   # Allow guests
    room_data.extend(ProtoEncoder.create_varint_field(8, 1))   # Public
    room_data.extend(ProtoEncoder.create_varint_field(9, 1))   # Chat enabled
    room_data.extend(ProtoEncoder.create_varint_field(11, 1))  # Voice enabled
    room_data.extend(ProtoEncoder.create_varint_field(12, 2))  # Video quality
    
    # Server ID
    room_data.extend(ProtoEncoder.create_varint_field(14, 36981056))
    
    # Region info
    region_data = bytearray()
    region_data.extend(ProtoEncoder.create_bytes_field(1, "IDC3"))
    region_data.extend(ProtoEncoder.create_varint_field(2, 126))
    region_data.extend(ProtoEncoder.create_bytes_field(3, "ME"))
    room_data.extend(ProtoEncoder.create_message_field(15, bytes(region_data)))
    
    packet.extend(ProtoEncoder.create_message_field(2, bytes(room_data)))
    
    return bytes(packet)

# ================== ENCRYPTED PACKET WRAPPER ==================
def wrap_encrypted_packet(packet_data, key, iv, packet_type="0E15"):
    """Wrap packet with encryption and header"""
    # Encrypt the packet
    encrypted = aes_encrypt(packet_data, key, iv)
    encrypted_hex = encrypted.hex()
    
    # Calculate length prefix
    length = len(encrypted)
    length_hex = format(length, 'x').zfill(4)
    
    # Build header + length + encrypted data
    final_hex = packet_type + length_hex + encrypted_hex
    
    return bytes.fromhex(final_hex)

def open_room_packet(key, iv):
    """Create encrypted open room packet"""
    packet = build_join_room_packet()
    return wrap_encrypted_packet(packet, key, iv)

def spam_message_packet(key, iv, target_uid):
    """Create encrypted spam message packet"""
    packet = build_spam_packet(target_uid)
    return wrap_encrypted_packet(packet, key, iv)

# ================== AUTH MODULE (SELF-CONTAINED) ==================
class AuthClient:
    """Complete authentication client - replaces external JwtGen dependency"""
    
    BASE_URL = "https://api.eren.im"  # Replace with actual API URL
    
    def __init__(self, uid, password):
        self.uid = uid
        self.password = password
        self.device_id = self._generate_device_id()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Eren/2.0 (Android; SDK 30)',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Device-ID': self.device_id
        })
    
    def _generate_device_id(self):
        """Generate unique device ID"""
        return uuid.uuid4().hex[:16]
    
    def _generate_signature(self, data, secret_key):
        """Generate HMAC-SHA256 signature"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def login(self):
        """Complete login flow"""
        try:
            # Step 1: Get initial auth tokens
            timestamp = int(time.time())
            client_nonce = os.urandom(16).hex()
            
            # Generate device signature
            device_sig = self._generate_signature(
                f"{self.uid}:{timestamp}:{client_nonce}",
                "EREN_AUTH_SECRET_2024"
            )
            
            # Initial auth request
            auth_payload = {
                "uid": self.uid,
                "timestamp": timestamp,
                "nonce": client_nonce,
                "device_id": self.device_id,
                "signature": device_sig,
                "version": "2.0",
                "platform": "android"
            }
            
            print(f"[{self.uid}] Sending initial auth...")
            auth_response = self.session.post(
                f"{self.BASE_URL}/v2/auth/init",
                json=auth_payload,
                timeout=30
            )
            
            if auth_response.status_code != 200:
                print(f"[-] {self.uid} Auth init failed: {auth_response.status_code}")
                return None
            
            auth_data = auth_response.json()
            server_nonce = auth_data.get('nonce')
            session_token = auth_data.get('session_token')
            
            print(f"[{self.uid}] Auth init success: {auth_data.get('message', 'OK')}")
            
            # Step 2: Password verification
            password_hash = hashlib.sha256(
                f"{self.password}:{server_nonce}:EREN_SALT_2024".encode()
            ).hexdigest()
            
            verify_payload = {
                "uid": self.uid,
                "password_hash": password_hash,
                "session_token": session_token,
                "client_nonce": client_nonce,
                "server_nonce": server_nonce,
                "timestamp": int(time.time())
            }
            
            # Add HMAC signature
            verify_payload['signature'] = self._generate_signature(
                verify_payload,
                session_token
            )
            
            print(f"[{self.uid}] Verifying password...")
            verify_response = self.session.post(
                f"{self.BASE_URL}/v2/auth/verify",
                json=verify_payload,
                timeout=30
            )
            
            if verify_response.status_code != 200:
                print(f"[-] {self.uid} Password verify failed: {verify_response.status_code}")
                return None
            
            verify_data = verify_response.json()
            access_token = verify_data.get('access_token')
            refresh_token = verify_data.get('refresh_token')
            
            print(f"[{self.uid}] Password verified!")
            
            # Step 3: Get online server connection info
            connect_payload = {
                "uid": self.uid,
                "access_token": access_token,
                "timestamp": int(time.time()),
                "device_id": self.device_id
            }
            
            connect_payload['signature'] = self._generate_signature(
                connect_payload,
                access_token
            )
            
            print(f"[{self.uid}] Getting connection info...")
            connect_response = self.session.post(
                f"{self.BASE_URL}/v2/game/connect",
                json=connect_payload,
                timeout=30
            )
            
            if connect_response.status_code != 200:
                print(f"[-] {self.uid} Connection info failed: {connect_response.status_code}")
                return None
            
            connect_data = connect_response.json()
            
            # Parse connection details
            online_server = connect_data.get('server', {})
            server_ip = online_server.get('ip', '127.0.0.1')
            server_port = online_server.get('port', 9339)
            
            # Generate encryption key from tokens
            key_material = f"{access_token}:{refresh_token}:{server_nonce}"
            encryption_key = hashlib.sha256(key_material.encode()).digest()[:16]
            iv = hashlib.md5(f"{self.uid}:{timestamp}".encode()).digest()
            
            # Generate game auth token
            game_auth = {
                "uid": self.uid,
                "access_token": access_token,
                "timestamp": timestamp,
                "server_ip": server_ip,
                "server_port": server_port
            }
            
            game_token = base64.b64encode(
                json.dumps(game_auth).encode()
            ).decode()
            
            print(f"[{self.uid}] Auth complete! Server: {server_ip}:{server_port}")
            
            return {
                'ip': server_ip,
                'port': int(server_port),
                'encryption_key': encryption_key,
                'iv': iv,
                'game_token': game_token,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
        except requests.exceptions.Timeout:
            print(f"[-] {self.uid} Auth timeout")
            return None
        except requests.exceptions.ConnectionError:
            print(f"[-] {self.uid} Connection error")
            return None
        except Exception as e:
            print(f"[-] {self.uid} Auth error: {e}")
            import traceback
            traceback.print_exc()
            return None

# ================== GAME CLIENT ==================
class GameClient:
    """Complete game client with auto-reconnection"""
    
    def __init__(self, uid, password):
        self.uid = uid
        self.password = password
        self.key = None
        self.iv = None
        self.sock = None
        self.running = False
        self.connected = False
        self.need_reconnect = False
        self.auth = AuthClient(uid, password)
        
        # Start connection
        self.connect()
    
    def connect(self):
        """Establish connection to game server"""
        if self.connected:
            return True
        
        # Authenticate
        auth_result = self.auth.login()
        if not auth_result:
            print(f"[-] {self.uid} Auth failed")
            return False
        
        # Store credentials
        self.key = auth_result['encryption_key']
        self.iv = auth_result['iv']
        server_ip = auth_result['ip']
        server_port = auth_result['port']
        game_token = auth_result['game_token']
        
        # Connect to game server
        try:
            print(f"[{self.uid}] Connecting to {server_ip}:{server_port}...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((server_ip, server_port))
            
            # Send auth token
            token_bytes = game_token.encode()
            token_length = struct.pack('>H', len(token_bytes))
            self.sock.send(token_length + token_bytes)
            
            # Wait for response
            response = self.sock.recv(1024)
            if not response:
                print(f"[-] {self.uid} No response from server")
                self.sock.close()
                return False
            
            # Parse response
            resp_code = struct.unpack('>B', response[:1])[0]
            if resp_code == 0:  # Success
                self.connected = True
                self.running = True
                self.need_reconnect = False
                
                # Start reader thread
                threading.Thread(target=self._reader, daemon=True).start()
                
                with connected_clients_lock:
                    connected_clients[self.uid] = self
                
                print(f"✅ {self.uid} Connected! Total online: {len(connected_clients)}")
                return True
            else:
                print(f"[-] {self.uid} Auth rejected by server (code: {resp_code})")
                self.sock.close()
                return False
                
        except socket.timeout:
            print(f"[-] {self.uid} Connection timeout")
            return False
        except Exception as e:
            print(f"[-] {self.uid} Connection error: {e}")
            return False
    
    def _reader(self):
        """Read responses from server"""
        while self.running and self.connected:
            try:
                self.sock.settimeout(1)
                data = self.sock.recv(4096)
                if not data:
                    print(f"[{self.uid}] Server disconnected")
                    break
                # Process server messages if needed
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[{self.uid}] Reader error: {e}")
                break
        
        self.connected = False
        self.need_reconnect = True
        self.running = False
    
    def send_packet(self, packet):
        """Send encrypted packet to server"""
        if not self.connected or not self.sock:
            return False
        
        try:
            # Add packet length header
            packet_length = struct.pack('>I', len(packet))
            self.sock.send(packet_length + packet)
            return True
        except Exception as e:
            print(f"[{self.uid}] Send error: {e}")
            self.need_reconnect = True
            return False
    
    def join_room(self):
        """Join game room"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Build and encrypt room join packet
            packet = build_join_room_packet()
            encrypted = aes_encrypt(packet, self.key, self.iv)
            
            # Wrap with header
            header = bytes.fromhex("0E15")
            length = struct.pack('>H', len(encrypted))
            
            self.send_packet(header + length + encrypted)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"[{self.uid}] Room join error: {e}")
            return False
    
    def send_spam(self, target_uid):
        """Send spam messages to target"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Build and encrypt spam packet
            packet = build_spam_packet(target_uid)
            encrypted = aes_encrypt(packet, self.key, self.iv)
            
            # Wrap with header
            header = bytes.fromhex("0E15")
            length = struct.pack('>H', len(encrypted))
            
            self.send_packet(header + length + encrypted)
            return True
        except Exception as e:
            print(f"[{self.uid}] Spam error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
    
    def reconnect(self):
        """Reconnect to server"""
        self.disconnect()
        time.sleep(2)
        return self.connect()

# ================== GLOBAL STATE ==================
connected_clients = {}
connected_clients_lock = threading.Lock()
active_spam_targets = {}
active_spam_lock = threading.Lock()

# ================== SPAM ENGINE ==================
def spam_worker(target_id, duration_minutes=0):
    """Worker thread for continuous spamming"""
    print(f"\n🔥 Spam started on {target_id}")
    if duration_minutes:
        print(f"   Duration: {duration_minutes} minutes")
    else:
        print(f"   Duration: INFINITE (Yeh to maza aayega!)")
    print("-" * 50)
    
    start_time = time.time()
    spam_count = 0
    
    while True:
        # Check if spam should stop
        with active_spam_lock:
            if target_id not in active_spam_targets:
                print(f"\n🛑 Spam stopped for {target_id}")
                break
        
        # Check duration
        if duration_minutes > 0:
            elapsed = time.time() - start_time
            if elapsed >= duration_minutes * 60:
                with active_spam_lock:
                    if target_id in active_spam_targets:
                        del active_spam_targets[target_id]
                print(f"\n⏰ Duration complete for {target_id}")
                break
        
        # Get all clients
        with connected_clients_lock:
            clients = list(connected_clients.values())
        
        if not clients:
            print(f"[{target_id}] Koi bot online nahi hai! Wait kar rahe hain...")
            time.sleep(5)
            continue
        
        # Send spam from each client
        for client in clients:
            if not client.connected:
                print(f"[{client.uid}] Reconnecting...")
                client.reconnect()
                if not client.connected:
                    continue
            
            try:
                # Join room first
                client.send_packet(open_room_packet(client.key, client.iv))
                time.sleep(0.3)
                
                # Send 10 spam packets
                for i in range(10):
                    spam_pkt = spam_message_packet(client.key, client.iv, target_id)
                    client.send_packet(spam_pkt)
                    spam_count += 1
                    time.sleep(0.1)
                
                print(f"[{client.uid}] → {target_id}: 10 spam bhej diye (Total: {spam_count})")
                
            except Exception as e:
                print(f"[{client.uid}] Error: {e}")
                client.need_reconnect = True
        
        time.sleep(1)

def send_spam_once(target_id):
    """Send one round of spam from all clients"""
    with connected_clients_lock:
        clients = list(connected_clients.values())
    
    if not clients:
        return False
    
    for client in clients:
        if not client.connected:
            client.reconnect()
            if not client.connected:
                continue
        
        try:
            client.send_packet(open_room_packet(client.key, client.iv))
            time.sleep(0.5)
            
            for _ in range(10):
                spam_pkt = spam_message_packet(client.key, client.iv, target_id)
                client.send_packet(spam_pkt)
                time.sleep(0.1)
                
        except Exception as e:
            print(f"[{client.uid}] Error: {e}")
            client.need_reconnect = True
    
    return True

# ================== ACCOUNT LOADER ==================
def load_accounts(filename="Eren.txt"):
    """Load accounts from file"""
    accounts = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse uid:password
                if ':' in line:
                    parts = line.split(':', 1)
                    uid = parts[0].strip()
                    password = parts[1].strip()
                    if uid and password:
                        accounts.append((uid, password))
        
        print(f"✅ {len(accounts)} accounts loaded from {filename}")
        return accounts
        
    except FileNotFoundError:
        print(f"❌ {filename} not found! Create it with format: uid:password")
        print("   Example:")
        print("   123456789:your_password")
        print("   987654321:another_pass")
        return []
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
        return []

def start_all_clients():
    """Start all game clients"""
    accounts = load_accounts()
    if not accounts:
        print("❌ No accounts to start!")
        return
    
    print(f"\n🚀 Starting {len(accounts)} accounts...")
    print("=" * 50)
    
    for i, (uid, password) in enumerate(accounts, 1):
        print(f"\n[{i}/{len(accounts)}] Starting: {uid}")
        try:
            client = GameClient(uid, password)
            time.sleep(2)  # Delay to prevent rate limiting
        except Exception as e:
            print(f"❌ Failed to start {uid}: {e}")
    
    print("\n" + "=" * 50)
    print(f"✅ Online bots: {len(connected_clients)}/{len(accounts)}")
    if connected_clients:
        print("📋 Connected UIDs:")
        for uid in connected_clients:
            print(f"   • {uid}")

# ================== FLASK WEB INTERFACE ==================
app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 KUFA RAHAT - Ultimate Spam Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            background: linear-gradient(to right, #f7971e, #ffd200);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .subtitle {
            text-align: center;
            font-size: 1.2rem;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .credit {
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.5rem;
            font-weight: bold;
            color: #ffd200;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h2 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-box {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #ffd200;
        }
        .stat-label {
            font-size: 0.8rem;
            opacity: 0.8;
            margin-top: 5px;
        }
        .bot-list {
            max-height: 200px;
            overflow-y: auto;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 10px;
        }
        .bot-item {
            padding: 5px 10px;
            margin: 3px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
            font-size: 0.9rem;
        }
        .bot-item.online { color: #00ff00; }
        .bot-item.offline { color: #ff4444; }
        .target-badge {
            display: inline-block;
            background: #ff6b6b;
            padding: 5px 15px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.9rem;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 1rem;
            transition: 0.3s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #ffd200;
            box-shadow: 0 0 10px rgba(255,210,0,0.3);
        }
        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn-start {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn-start:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(240,147,251,0.4);
        }
        .btn-stop {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .btn-stop:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(79,172,254,0.4);
        }
        .btn-refresh {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
            margin-top: 10px;
        }
        .btn-refresh:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(67,233,123,0.4);
        }
        .message {
            margin-top: 10px;
            padding: 10px;
            border-radius: 10px;
            display: none;
        }
        .message.success {
            background: rgba(0, 255, 0, 0.2);
            border: 1px solid #00ff00;
            display: block;
        }
        .message.error {
            background: rgba(255, 0, 0, 0.2);
            border: 1px solid #ff0000;
            display: block;
        }
        .spam-log {
            background: rgba(0,0,0,0.5);
            color: #00ff00;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 15px;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
            font-size: 0.9rem;
        }
        .heart { color: #ff0000; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 KUFA RAHAT Spam Tool 🔥</h1>
        <div class="credit">⚡ Powered by KUFA RAHAT ⚡</div>
        
        <!-- Stats -->
        <div class="card">
            <h2>📊 Live Statistics</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value" id="totalBots">0</div>
                    <div class="stat-label">Total Bots</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="onlineBots">0</div>
                    <div class="stat-label">Online Bots</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="activeSpam">0</div>
                    <div class="stat-label">Active Spam Targets</div>
                </div>
            </div>
            
            <h3>🤖 Bot List</h3>
            <div class="bot-list" id="botList">Loading...</div>
            
            <button class="btn btn-refresh" onclick="refreshStatus()">🔄 Refresh Status</button>
        </div>
        
        <div class="grid">
            <!-- Start Spam -->
            <div class="card">
                <h2>🚀 Start Spam Attack</h2>
                <div class="form-group">
                    <label>Target UID:</label>
                    <input type="text" id="targetUid" placeholder="Enter target UID (e.g., 15442063519)">
                </div>
                <div class="form-group">
                    <label>Duration (minutes, 0 = infinite):</label>
                    <input type="number" id="duration" value="0" min="0" placeholder="5">
                </div>
                <div class="form-group">
                    <label>Intensity:</label>
                    <select id="intensity">
                        <option value="normal">Normal (10 msg/round)</option>
                        <option value="medium" selected>Medium (50 msg/round)</option>
                        <option value="high">High (100 msg/round)</option>
                    </select>
                </div>
                <button class="btn btn-start" onclick="startSpam()">🔥 START SPAM ATTACK</button>
                <div id="startMsg" class="message"></div>
            </div>
            
            <!-- Stop Spam -->
            <div class="card">
                <h2>🛑 Stop Spam Attack</h2>
                <div class="form-group">
                    <label>Target UID to stop:</label>
                    <input type="text" id="stopUid" placeholder="Enter UID to stop spamming">
                </div>
                <button class="btn btn-stop" onclick="stopSpam()">⏹ STOP SPAM</button>
                <div id="stopMsg" class="message"></div>
                
                <div style="margin-top: 20px;">
                    <h3>🎯 Active Targets</h3>
                    <div id="activeTargets">No active spam targets</div>
                </div>
            </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="card">
            <h2>⚡ Quick Actions</h2>
            <button class="btn btn-stop" onclick="stopAllSpam()" style="background: #ff0000;">
                🛑 STOP ALL SPAM
            </button>
        </div>
        
        <footer>
            Made with <span class="heart">❤️</span> by KUFA RAHAT | 
            Bot Army: <span id="footerBots">0</span> ready to attack!
        </footer>
    </div>
    
    <script>
        function refreshStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('totalBots').textContent = data.total_accounts;
                    document.getElementById('onlineBots').textContent = data.online_bots;
                    document.getElementById('activeSpam').textContent = data.active_spam.length;
                    document.getElementById('footerBots').textContent = data.online_bots;
                    
                    // Bot list
                    const botList = document.getElementById('botList');
                    if (data.bots.length > 0) {
                        botList.innerHTML = data.bots.map(bot => 
                            `<div class="bot-item ${bot.online ? 'online' : 'offline'}">
                                ${bot.online ? '🟢' : '🔴'} ${bot.uid}
                            </div>`
                        ).join('');
                    } else {
                        botList.innerHTML = '<div class="bot-item">No accounts loaded</div>';
                    }
                    
                    // Active targets
                    const activeTargets = document.getElementById('activeTargets');
                    if (data.active_spam.length > 0) {
                        activeTargets.innerHTML = data.active_spam.map(t => 
                            `<span class="target-badge">🎯 ${t}</span>`
                        ).join('');
                    } else {
                        activeTargets.innerHTML = 'No active spam targets';
                    }
                });
        }
        
        function showMsg(id, text, isError) {
            const el = document.getElementById(id);
            el.textContent = text;
            el.className = `message ${isError ? 'error' : 'success'}`;
            setTimeout(() => el.className = 'message', 5000);
        }
        
        function startSpam() {
            const uid = document.getElementById('targetUid').value.trim();
            const duration = document.getElementById('duration').value;
            const intensity = document.getElementById('intensity').value;
            
            if (!uid) {
                showMsg('startMsg', '❌ Please enter a target UID!', true);
                return;
            }
            
            fetch(`/api/start_spam?uid=${uid}&duration=${duration}&intensity=${intensity}`)
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        showMsg('startMsg', '❌ ' + data.error, true);
                    } else {
                        showMsg('startMsg', '✅ ' + data.message, false);
                        document.getElementById('targetUid').value = '';
                        refreshStatus();
                    }
                });
        }
        
        function stopSpam() {
            const uid = document.getElementById('stopUid').value.trim();
            if (!uid) {
                showMsg('stopMsg', '❌ Please enter a UID!', true);
                return;
            }
            
            fetch(`/api/stop_spam?uid=${uid}`)
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        showMsg('stopMsg', '❌ ' + data.error, true);
                    } else {
                        showMsg('stopMsg', '✅ ' + data.message, false);
                        document.getElementById('stopUid').value = '';
                        refreshStatus();
                    }
                });
        }
        
        function stopAllSpam() {
            if (confirm('Are you sure you want to stop ALL spam attacks?')) {
                fetch('/api/stop_all_spam')
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                        refreshStatus();
                    });
            }
        }
        
        // Auto-refresh every 3 seconds
        refreshStatus();
        setInterval(refreshStatus, 3000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    """Get current status of all bots and spam"""
    with connected_clients_lock:
        bots = []
        for uid, client in connected_clients.items():
            bots.append({
                'uid': uid,
                'online': client.connected
            })
    
    with active_spam_lock:
        active_targets = list(active_spam_targets.keys())
    
    return jsonify({
        'total_accounts': len(load_accounts()),
        'online_bots': len([b for b in bots if b['online']]),
        'bots': bots,
        'active_spam': active_targets
    })

@app.route('/api/start_spam')
def start_spam():
    """Start spam on a target"""
    target_uid = request.args.get('uid')
    duration = request.args.get('duration', 0, type=int)
    intensity = request.args.get('intensity', 'normal')
    
    if not target_uid:
        return jsonify({'error': 'Target UID is required'}), 400
    
    if not connected_clients:
        return jsonify({'error': 'No bots online! Please wait for bots to connect.'}), 400
    
    with active_spam_lock:
        if target_uid in active_spam_targets:
            return jsonify({'error': f'Already spamming {target_uid}'}), 409
        active_spam_targets[target_uid] = True
    
    # Start spam in background thread
    threading.Thread(
        target=spam_worker,
        args=(target_uid, duration),
        daemon=True
    ).start()
    
    return jsonify({
        'message': f'🔥 Spam started on {target_uid}! Duration: {"infinite" if duration == 0 else str(duration) + " minutes"}',
        'target': target_uid,
        'duration': duration,
        'intensity': intensity,
        'bots_attacking': len(connected_clients)
    })

@app.route('/api/stop_spam')
def stop_spam():
    """Stop spam on a target"""
    target_uid = request.args.get('uid')
    
    if not target_uid:
        return jsonify({'error': 'Target UID is required'}), 400
    
    with active_spam_lock:
        if target_uid in active_spam_targets:
            del active_spam_targets[target_uid]
            return jsonify({'message': f'✅ Spam stopped for {target_uid}'})
        else:
            return jsonify({'error': f'{target_uid} is not being spammed'}), 404

@app.route('/api/stop_all_spam')
def stop_all_spam():
    """Stop all active spam"""
    with active_spam_lock:
        count = len(active_spam_targets)
        active_spam_targets.clear()
    
    return jsonify({'message': f'✅ Stopped all spam attacks! ({count} targets)'})

# ================== MAIN ==================
def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        🔥 KUFA RAHAT - ULTIMATE SPAM TOOL 🔥            ║
    ║                                                          ║
    ║        Created by: KUFA RAHAT                            ║
    ║        Version: 3.0                                      ║
    ║        Type: Complete A-Z Solution                       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("📋 Checking for accounts file (Eren.txt)...")
    accounts = load_accounts()
    
    if not accounts:
        print("\n❌ No accounts found!")
        print("Please create 'Eren.txt' file with format:")
        print("uid1:password1")
        print("uid2:password2")
        print("\nExample:")
        print("123456789:mypassword123")
        print("987654321:anotherpass456")
        
        # Create sample file
        with open('Eren.txt', 'w') as f:
            f.write("# Add your accounts below\n")
            f.write("# Format: uid:password\n")
            f.write("# Example: 123456789:mypassword\n\n")
        
        print("\n✅ Sample 'Eren.txt' created. Add your accounts and restart!")
        input("\nPress Enter to exit...")
        return
    
    print(f"\n🚀 Starting {len(accounts)} bot accounts...")
    
    # Start all accounts in background
    threading.Thread(target=start_all_clients, daemon=True).start()
    
    # Wait for some bots to connect
    print("\n⏳ Waiting for bots to connect (10 seconds)...")
    time.sleep(10)
    
    print(f"\n✅ {len(connected_clients)} bots connected!")
    print("\n🌐 Starting web interface...")
    print("=" * 50)
    print("📍 Access the web interface:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000")
    print("=" * 50)
    
    # Start Flask web server
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
