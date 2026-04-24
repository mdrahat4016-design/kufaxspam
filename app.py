import os, time, json, random, socket, threading, asyncio
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Import authentication functions
from JwtGen import (
    GeNeRaTeAccEss, EncRypTMajoRLoGin, MajorLogin, DecRypTMajoRLoGin,
    GetLoginData, DecRypTLoGinDaTa, xAuThSTarTuP
)

# ---------- Global data ----------
connected_clients = {}          # uid -> client object
connected_clients_lock = threading.Lock()
active_spam_targets = {}        # target uid -> True
active_spam_lock = threading.Lock()

# ---------- Packet functions ----------
def EnC_Uid(H):
    e, H = [], int(H)
    while H:
        e.append((H & 0x7F) | (0x80 if H > 0x7F else 0))
        H >>= 7
    return bytes(e).hex()

def CrEaTe_ProTo(fields):
    def EnC_Vr(N):
        if N < 0:
            return b''
        H = []
        while True:
            b = N & 0x7F
            N >>= 7
            if N:
                b |= 0x80
            H.append(b)
            if not N:
                break
        return bytes(H)
    def CrEaTe_VarianT(field_number, value):
        field_header = (field_number << 3) | 0
        return EnC_Vr(field_header) + EnC_Vr(value)
    def CrEaTe_LenGTh(field_number, value):
        field_header = (field_number << 3) | 2
        encoded_value = value.encode() if isinstance(value, str) else value
        return EnC_Vr(field_header) + EnC_Vr(len(encoded_value)) + encoded_value
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested = CrEaTe_ProTo(value)
            packet.extend(CrEaTe_LenGTh(field, nested))
        elif isinstance(value, int):
            packet.extend(CrEaTe_VarianT(field, value))
        elif isinstance(value, (str, bytes)):
            packet.extend(CrEaTe_LenGTh(field, value))
    return packet

def GeneRaTePk(Pk, N, K, V):
    def EnC_PacKeT(HeX, K, V):
        return AES.new(K, AES.MODE_CBC, V).encrypt(pad(bytes.fromhex(HeX), 16)).hex()
    def DecodE_HeX(H):
        return hex(H)[2:].zfill(2)
    PkEnc = EnC_PacKeT(Pk, K, V)
    _ = DecodE_HeX(len(PkEnc) // 2)
    if len(_) == 2:
        HeadEr = N + "000000"
    elif len(_) == 3:
        HeadEr = N + "00000"
    elif len(_) == 4:
        HeadEr = N + "0000"
    elif len(_) == 5:
        HeadEr = N + "000"
    else:
        HeadEr = N + "000000"
    return bytes.fromhex(HeadEr + _ + PkEnc)

def openroom(K, V):
    fields = {
        1: 2,
        2: {
            1: 1, 2: 15, 3: 5, 4: "EREN_CORE", 5: "1", 6: 12, 7: 1, 8: 1, 9: 1,
            11: 1, 12: 2, 14: 36981056,
            15: {1: "IDC3", 2: 126, 3: "ME"},
            16: "\u0001\u0003\u0004\u0007\t\n\u000b\u0012\u000f\u000e\u0016\u0019\u001a \u001d",
            18: 2368584, 27: 1, 34: "\u0000\u0001", 40: "en", 48: 1,
            49: {1: 21}, 50: {1: 36981056, 2: 2368584, 5: 2}
        }
    }
    return GeneRaTePk(CrEaTe_ProTo(fields).hex(), '0E15', K, V)

def spmroom(K, V, uid):
    fields = {1: 22, 2: {1: int(uid)}}
    return GeneRaTePk(CrEaTe_ProTo(fields).hex(), '0E15', K, V)

# ---------- Spam worker with reconnection ----------
def send_spam_from_all_accounts(target_id):
    with connected_clients_lock:
        clients = list(connected_clients.values())
    for client in clients:
        # If socket is dead, try to reconnect
        if not client.online_sock or client._need_reconnect:
            print(f"[{client.uid}] Reconnecting...")
            client.reconnect()
            if not client.online_sock:
                continue
        try:
            client.online_sock.send(openroom(client.key, client.iv))
            print(f"[{client.uid}] Room khola")
            time.sleep(1.5)
            for i in range(10):
                client.online_sock.send(spmroom(client.key, client.iv, target_id))
                print(f"[{client.uid}] {target_id} ko spam bheja - {i+1}")
                time.sleep(0.2)
        except (BrokenPipeError, OSError) as e:
            print(f"[{client.uid}] Error: {e} -> reconnecting")
            client._need_reconnect = True
        except Exception as e:
            print(f"[{client.uid}] Other error: {e}")

def spam_worker(target_id, duration_minutes):
    print(f"Target {target_id} pe spam start ({duration_minutes} min)")
    start_time = datetime.now()
    while True:
        with active_spam_lock:
            if target_id not in active_spam_targets:
                break
            if duration_minutes:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= duration_minutes * 60:
                    del active_spam_targets[target_id]
                    break
        try:
            send_spam_from_all_accounts(target_id)
            time.sleep(1)
        except Exception as e:
            print(f"Spam error: {e}")
            time.sleep(1)

# ---------- Account client with auto-reconnect ----------
class FF_CLient:
    def __init__(self, uid, password):
        self.uid = uid
        self.password = password
        self.key = None
        self.iv = None
        self.auth_token = None
        self.online_sock = None
        self.running = False
        self._need_reconnect = False
        self._connect()

    def _run_async(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _full_auth(self):
        open_id, access_token = self._run_async(GeNeRaTeAccEss(self.uid, self.password))
        if not open_id or not access_token:
            return False
        payload = self._run_async(EncRypTMajoRLoGin(open_id, access_token))
        login_res = self._run_async(MajorLogin(payload))
        if not login_res:
            return False
        dec = self._run_async(DecRypTMajoRLoGin(login_res))
        self.key = dec.key
        self.iv = dec.iv
        token = dec.token
        timestamp = dec.timestamp
        account_uid = dec.account_uid
        login_data = self._run_async(GetLoginData(dec.url, payload, token))
        if not login_data:
            return False
        ports = self._run_async(DecRypTLoGinDaTa(login_data))
        online_ip, online_port = ports.Online_IP_Port.split(":")
        self.online_ip = online_ip
        self.online_port = int(online_port)
        self.auth_token = self._run_async(xAuThSTarTuP(
            int(account_uid), token, int(timestamp), self.key, self.iv
        ))
        return True

    def _connect_online(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.online_ip, self.online_port))
        sock.send(bytes.fromhex(self.auth_token))
        resp = sock.recv(4096)
        if not resp:
            sock.close()
            return None
        print(f"[+] {self.uid} Online connected")
        return sock

    def _reader(self, sock):
        while self.running:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                # Optionally handle responses (not needed for spam)
            except Exception as e:
                print(f"[{self.uid}] Reader error: {e}")
                break
        self.running = False
        self._need_reconnect = True

    def _connect(self):
        if not self._full_auth():
            print(f"[-] {self.uid} Auth failed")
            return
        sock = self._connect_online()
        if not sock:
            return
        self.online_sock = sock
        self.running = True
        self._need_reconnect = False
        threading.Thread(target=self._reader, args=(sock,), daemon=True).start()
        with connected_clients_lock:
            connected_clients[self.uid] = self
            print(f"Account {self.uid} online aa gaya. Total: {len(connected_clients)}")

    def reconnect(self):
        """Close old socket and reconnect."""
        if self.online_sock:
            try:
                self.online_sock.close()
            except:
                pass
        self.running = False
        self._connect()

# ---------- Load accounts from Eren.txt ----------
def load_accounts():
    accounts = []
    try:
        with open("Eren.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line and not line.startswith("#"):
                    uid, pwd = line.split(":", 1)
                    accounts.append((uid, pwd))
    except FileNotFoundError:
        print("Eren.txt nahi mili")
    return accounts

def start_all_accounts():
    for uid, pwd in load_accounts():
        threading.Thread(target=lambda: FF_CLient(uid, pwd), daemon=True).start()
        time.sleep(3)

# ---------- Flask Web App (Hinglish, KUFA RAHAT) ----------
app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KUFA RAHAT Spam Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5rem;
            background: linear-gradient(90deg, #ff416c, #ff4b2b);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .credit {
            text-align: center;
            margin-bottom: 30px;
            font-size: 1rem;
            opacity: 0.8;
        }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h2 {
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-left: 4px solid #ff416c;
            padding-left: 15px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #ff416c;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        .account-list {
            max-height: 200px;
            overflow-y: auto;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 10px;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .account-item {
            padding: 5px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .form-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: flex-end;
        }
        .input-field {
            flex: 1;
            min-width: 200px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-size: 0.8rem;
            opacity: 0.8;
        }
        input {
            width: 100%;
            padding: 12px 15px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            color: white;
            font-size: 1rem;
            outline: none;
            transition: 0.3s;
        }
        input:focus {
            border-color: #ff416c;
            box-shadow: 0 0 10px rgba(255,65,108,0.3);
        }
        button {
            padding: 12px 25px;
            background: linear-gradient(90deg, #ff416c, #ff4b2b);
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            font-size: 1rem;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255,65,108,0.4);
        }
        .stop-btn {
            background: linear-gradient(90deg, #4a4a4a, #2c2c2c);
        }
        .stop-btn:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.4);
        }
        .message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 10px;
            display: none;
        }
        .message.success {
            background: rgba(0,255,0,0.2);
            border: 1px solid #00ff00;
            display: block;
        }
        .message.error {
            background: rgba(255,0,0,0.2);
            border: 1px solid #ff0000;
            display: block;
        }
        .active-targets {
            margin-top: 15px;
        }
        .target-badge {
            display: inline-block;
            background: #ff416c;
            padding: 5px 12px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.8rem;
        }
        hr {
            border-color: rgba(255,255,255,0.1);
            margin: 15px 0;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            opacity: 0.6;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🔥 KUFA RAHAT Spam Tool 🔥</h1>
    <div class="credit">⚡ Credit: KUFA RAHAT ⚡</div>

    <!-- Status Card -->
    <div class="card">
        <h2>📊 Status</h2>
        <div class="status-grid">
            <div class="stat-card">
                <div class="stat-number" id="accCount">0</div>
                <div class="stat-label">Bot online aa gaye</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="activeSpamCount">0</div>
                <div class="stat-label">Active spam chal raha</div>
            </div>
        </div>
        <div>
            <strong>📋 Connected bots:</strong>
            <div class="account-list" id="accountList">
                Loading...
            </div>
        </div>
        <div class="active-targets" id="activeTargetsDiv">
            <strong>🎯 Jahan spam chal raha:</strong>
            <div id="activeTargets"></div>
        </div>
    </div>

    <!-- Start Spam Card -->
    <div class="card">
        <h2>🚀 NEW SPAM UID</h2>
        <div class="form-group">
            <div class="input-field">
                <label>Target ka uid daal</label>
                <input type="text" id="targetUid" placeholder="Jaise 15442063519">
            </div>
            <div class="input-field">
                <label>Kitne minute tak? (chhod do to infinite)</label>
                <input type="number" id="duration" placeholder="Jaise 5">
            </div>
            <button id="startBtn">▶ Spsam start</button>
        </div>
        <div id="startMessage" class="message"></div>
    </div>

    <!-- Stop Spam Card -->
    <div class="card">
        <h2>🛑 SPAM OFF</h2>
        <div class="form-group">
            <div class="input-field">
                <label>Jiska spam band karna hai uska uid daal</label>
                <input type="text" id="stopTargetUid" placeholder="Jaise 15442063519">
            </div>
            <button id="stopBtn" class="stop-btn">⏹ SPAM OFF</button>
        </div>
        <div id="stopMessage" class="message"></div>
    </div>

    <footer>
        ⚡ Har bot 10 packet bhejega per round, har minute round repeat hoga ⚡<br>
        Made with ❤️ by KUFA RAHAT
    </footer>
</div>

<script>
    function fetchStatus() {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('accCount').innerText = data.connected_accounts;
                document.getElementById('activeSpamCount').innerText = data.active_spam.length;
                const accListDiv = document.getElementById('accountList');
                if (data.accounts && data.accounts.length) {
                    accListDiv.innerHTML = data.accounts.map(acc => `<div class="account-item">📱 ${acc}</div>`).join('');
                } else {
                    accListDiv.innerHTML = '<div class="account-item">Koi bot online nahi</div>';
                }
                const targetsDiv = document.getElementById('activeTargets');
                if (data.active_spam.length) {
                    targetsDiv.innerHTML = data.active_spam.map(t => `<span class="target-badge">${t}</span>`).join('');
                } else {
                    targetsDiv.innerHTML = '<span style="opacity:0.7;">Koi active spam nahi</span>';
                }
            })
            .catch(err => console.error(err));
    }

    function showMessage(elementId, text, isError = false) {
        const el = document.getElementById(elementId);
        el.innerText = text;
        el.className = 'message ' + (isError ? 'error' : 'success');
        setTimeout(() => {
            el.className = 'message';
        }, 3000);
    }

    document.getElementById('startBtn').onclick = () => {
        const uid = document.getElementById('targetUid').value.trim();
        const duration = document.getElementById('duration').value.trim();
        if (!uid) {
            showMessage('startMessage', 'Bhai uid to daal', true);
            return;
        }
        const url = `/start_spam?uid=${encodeURIComponent(uid)}` + (duration ? `&duration=${parseInt(duration)}` : '');
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    showMessage('startMessage', data.error, true);
                } else {
                    showMessage('startMessage', `✅ ${data.status} | Target: ${data.target} | Duration: ${data.duration_minutes || 'Infinite'} min`);
                    document.getElementById('targetUid').value = '';
                    document.getElementById('duration').value = '';
                    fetchStatus();
                }
            })
            .catch(err => showMessage('startMessage', 'Server error', true));
    };

    document.getElementById('stopBtn').onclick = () => {
        const uid = document.getElementById('stopTargetUid').value.trim();
        if (!uid) {
            showMessage('stopMessage', 'Bhai uid daal jiska spam band karna hai', true);
            return;
        }
        fetch(`/stop_spam?uid=${encodeURIComponent(uid)}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    showMessage('stopMessage', data.error, true);
                } else {
                    showMessage('stopMessage', `🛑 ${data.status}`);
                    document.getElementById('stopTargetUid').value = '';
                    fetchStatus();
                }
            })
            .catch(err => showMessage('stopMessage', 'Server error', true));
    };

    fetchStatus();
    setInterval(fetchStatus, 3000);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    with active_spam_lock:
        active = list(active_spam_targets.keys())
    with connected_clients_lock:
        acc_list = list(connected_clients.keys())
    return jsonify({
        'connected_accounts': len(connected_clients),
        'accounts': acc_list,
        'active_spam': active
    })

@app.route('/start_spam')
def start_spam_route():
    target = request.args.get('uid')
    duration = request.args.get('duration', type=int)
    if not target:
        return jsonify({'error': 'uid parameter chahiye'}), 400
    if not connected_clients:
        return jsonify({'error': 'Koi bot online nahi hai'}), 500
    with active_spam_lock:
        if target in active_spam_targets:
            return jsonify({'error': f'{target} pe already spam chal raha hai'}), 409
        active_spam_targets[target] = True
        threading.Thread(target=spam_worker, args=(target, duration), daemon=True).start()
    return jsonify({
        'status': 'Spam shuru kar diya',
        'target': target,
        'duration_minutes': duration
    })

@app.route('/stop_spam')
def stop_spam_route():
    target = request.args.get('uid')
    if not target:
        return jsonify({'error': 'uid parameter chahiye'}), 400
    with active_spam_lock:
        if target in active_spam_targets:
            del active_spam_targets[target]
            return jsonify({'status': f'{target} ka spam band kar diya'})
        else:
            return jsonify({'error': f'{target} pe koi spam nahi chal raha'}), 404

# ---------- Main ----------
if __name__ == '__main__':
    threading.Thread(target=start_all_accounts, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)