import requests , os , psutil , sys , jwt , pickle , json , binascii , time , urllib3 , base64 , datetime , re , socket , threading , ssl , pytz , aiohttp
from protobuf_decoder.protobuf_decoder import Parser
from Functions import * ; from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from Pb2 import DEcwHisPErMsG_pb2 , MajoRLoGinrEs_pb2 , PorTs_pb2 , MajoRLoGinrEq_pb2 , sQ_pb2 , Team_msg_pb2
from cfonts import render, say

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  


Chat_Leave = False
joining_team = False
login_url , ob , version = AuToUpDaTE()
login_url = "https://loginbp.ggpolarbear.com"


Hr = {
    'User-Agent': Uaa(),
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': ob}

# ---- Random Colores ----

def get_random_color():
    colors = [
        "[FF0000]", "[00FF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]",
        "[9932CC]", "[8A2BE2]", "[4B0082]", "[6A5ACD]", "[7B68EE]", "[4169E1]", "[1E90FF]", "[191970]",
        "[00008B]", "[000080]", "[008080]", "[008B8B]", "[B0E0E6]", "[AFEEEE]", "[E0FFFF]", "[F5F5DC]",
        "[FAEBD7]"
    ]
    return random.choice(colors)

async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    encrypted_payload = cipher.encrypt(padded_message)
    return encrypted_payload
    
async def GeNeRaTeAccEss(uid , password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": (await Ua()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"}
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=Hr, data=data) as response:
            if response.status != 200: return await response.read()
            data = await response.json()
            open_id = data.get("open_id")
            access_token = data.get("access_token")
            return (open_id, access_token) if open_id and access_token else (None, None)

async def EncRypTMajoRLoGin(open_id, access_token):
    major_login = MajoRLoGinrEq_pb2.MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = '2.124.1'
    major_login.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "280"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2019118695"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    string = major_login.SerializeToString()
    
    return  await encrypted_proto(string)

async def MajorLogin(payload):
    url = f"{login_url}/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    Hr['Authorization']= f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    proto = MajoRLoGinrEs_pb2.MajorLoginRes()
    proto.ParseFromString(MajoRLoGinResPonsE)
    return proto

async def DecRypTLoGinDaTa(LoGinDaTa):
    proto = PorTs_pb2.GetLoginData()
    proto.ParseFromString(LoGinDaTa)
    return proto

async def DecodeWhisperMessage(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = DEcwHisPErMsG_pb2.DecodeWhisper()
    proto.ParseFromString(packet)
    return proto
    
async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = sQ_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto
    
async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9: headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7: headers = '000000000'
    else: print('Unexpected length') ; headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"
     





class CLIENT:
    def __init__(self):
        self.whisper_writer = None
        self.online_writer = None
        self.uid = None
        self.room_uid = None
        self.response = None
        self.inPuTMsG = None
        self.chat_id = None
        self.data = None
        self.data2 = None
        self.key = None
        self.iv = None
        self.STATUS = None
        self.AutHToKen = None
        self.OnLineiP = None
        self.OnLineporT = None
        self.ChaTiP = None
        self.ChaTporT = None
        self.LoGinDaTaUncRypTinG = None

        self.response = None
        self.uid = None
        self.chat_id = None
        self.XX = None
        self.inPuTMsG = None
        self.insquad = None
        self.sent_inv = None
    async def cHTypE(self,H):
        if not H: return 'Squid'
        elif H == 1: return 'CLan'
        elif H == 2: return 'PrivaTe'
        
    async def SEndMsG(self,H , message , Uid , chat_id , key , iv):
        TypE = await self.cHTypE(H)
        if TypE == 'Squid': msg_packet = await xSEndMsgsQ(message , chat_id , key , iv)
        elif TypE == 'CLan': msg_packet = await xSEndMsg(message , 1 , chat_id , chat_id , key , iv)
        elif TypE == 'PrivaTe': msg_packet = await xSEndMsg(message , 2 , Uid , Uid , key , iv)
        return msg_packet

    async def SEndPacKeT(self,OnLinE , ChaT , TypE , PacKeT):
        if TypE == 'ChaT' and ChaT: self.whisper_writer.write(PacKeT) ; await self.whisper_writer.drain()
        elif TypE == 'OnLine': self.online_writer.write(PacKeT) ; await self.online_writer.drain()
        else: return 'UnsoPorTed TypE ! >> ErrrroR (:():)' 
           
    async def TcPOnLine(self,ip, port, key, iv, AutHToKen, reconnect_delay=0.5):
        global  spam_room , spammer_uid , spam_chat_id , spam_uid , XX , uid , Spy, Chat_Leave , joining_team
        while True:
            try:
                reader , writer = await asyncio.open_connection(ip, int(port))
                self.online_writer = writer
                bytes_payload = bytes.fromhex(AutHToKen)
                self.online_writer.write(bytes_payload)
                await self.online_writer.drain()
                while True:
                    self.data2 = await reader.read(9999)
                    #print(self.data2.hex())
                    data2 = self.data2
                    if not data2: break
                    
                    if self.data2:

                        if self.data2.hex().startswith("0f00"):
                            info = await DeCode_PackEt(self.data2.hex()[10:])
                            #print(info)
                            self.STATUS = get_player_status(info)
                            print(self.STATUS)
                            if "IN_ROOM" in self.STATUS:
                                room_uid = self.STATUS['room_uid']
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , await SendRoomInfo(int(room_uid),key,iv))
                            else:
                                message = self.STATUS
                                P = await self.SEndMsG(2 , message , uid , chat_id , key , iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)

                        if self.data2.hex().startswith("0e00"):
                            info = await DeCode_PackEt(self.data2.hex()[10:])
                            message = get_room_info(info)
                            P = await self.SEndMsG(2 , message , uid , chat_id , key , iv)
                            await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)



                            
                        #print(self.data2.hex())
                        if self.data2.hex().startswith("0500") and self.insquad is None and joining_team == False:
                            
                            packet = await DeCode_PackEt(self.data2.hex()[10:])
                            packet = json.loads(packet)


                                
                            try:
                                invite_uid = packet['5']['data']['2']['data']['1']['data']
                                squad_owner = packet['5']['data']['1']['data']

                                squad_code = packet['5']['data']['8']['data']

                                RefUse = await RedZedRefuse(squad_owner,invite_uid, key,iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , RefUse)
                                SendInv = await RedZed_SendInv(invite_uid,key,iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , SendInv)
                                self.insquad = False
                                    
                            except:
                                continue
                            if self.insquad == False:
                                Join = await RedZedAccepted(squad_owner,squad_code,key,iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , Join)
                                self.insquad = True

                        

                        if self.data2.hex().startswith('0500') and len(self.data2.hex()) > 1000 and joining_team:
                            try:

                                packet = await DeCode_PackEt(self.data2.hex()[10:])

                                packet = json.loads(packet)
                                OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet)
                                JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , JoinCHaT)
                                message = f'[B][C]{get_random_color()}\n- WeLComE To Emote Bot ! \n\n{get_random_color()}- Commands : @a {xMsGFixinG('123456789')} {xMsGFixinG('909000001')}\n\n[00FF00]Dev : @{xMsGFixinG('redzedking')}'
                                P = await self.SEndMsG(0 , message , OwNer_UiD , OwNer_UiD , key , iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)
                            except:
                                if self.data2.hex().startswith('0500') and len(self.data2.hex()) > 1000:
                                    try:

                                        packet = await DeCode_PackEt(self.data2.hex()[10:])

                                        packet = json.loads(packet)
                                        OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet)
                                        JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                                        await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , JoinCHaT)
                                        message = f'[B][C]{get_random_color()}\n- WeLComE To Emote Bot ! \n\n{get_random_color()}- Commands : @a {xMsGFixinG('123456789')} {xMsGFixinG('909000001')}\n\n[00FF00]Dev : @{xMsGFixinG('redzedking')}'
                                        P = await self.SEndMsG(0 , message , OwNer_UiD , OwNer_UiD , key , iv)
                                        await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)
                                    except:
                                        pass
                        joining_team = False

                if self.whisper_writer is not None:
                    try:
                        self.whisper_writer.close()
                        await self.whisper_writer.wait_closed()
                    except Exception as e:
                        print(f"Error closing whisper_writer: {e}")
                    finally:
                        self.whisper_writer = None

                if self.online_writer is not None:
                    try:
                        self.online_writer.close()
                        await self.online_writer.wait_closed()
                    except Exception as e:
                        print(f"Error closing online_writer: {e}")
                    finally:
                        self.online_writer = None

                self.insquad = None




            except Exception as e: print(f"- ErroR With {ip}:{port} - {e}") ; self.online_writer = None
            await asyncio.sleep(reconnect_delay)
                                
    async def TcPChaT(self,ip, port, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, reconnect_delay=0.5):

        global spam_room, spammer_uid , spam_chat_id , spam_uid , chat_id , uid , Spy, Chat_Leave , joining_team
        while True:
            try:
                reader , writer = await asyncio.open_connection(ip, int(port))
                self.whisper_writer = writer
                bytes_payload = bytes.fromhex(AutHToKen)
                self.whisper_writer.write(bytes_payload)
                await self.whisper_writer.drain()
                ready_event.set()
                if LoGinDaTaUncRypTinG.Clan_ID:
                    clan_id = LoGinDaTaUncRypTinG.Clan_ID
                    clan_compiled_data = LoGinDaTaUncRypTinG.Clan_Compiled_Data
                    print('\n - TarGeT BoT in CLan ! ')
                    print(f' - Clan Uid > {clan_id}')
                    print(f' - BoT ConnEcTed WiTh CLan ChaT SuccEssFuLy ! ')
                    pK = await AuthClan(clan_id , clan_compiled_data , key , iv)
                    if self.whisper_writer: self.whisper_writer.write(pK) ; await self.whisper_writer.drain()
                while True:
                    self.data = await reader.read(9999)
                    data=self.data


                    if not data: break



                    if data.hex().startswith("120000"):

                        msg = await DeCode_PackEt(data.hex()[10:])
                        chatdata = json.loads(msg)
                        try:
                            self.response = await DecodeWhisperMessage(data.hex()[10:])
                            uid = self.response.Data.uid
                            chat_id = self.response.Data.Chat_ID
                            self.XX = self.response.Data.chat_type
                            self.inPuTMsG = self.response.Data.msg.lower()
                        except:
                            self.response = None


                        if self.response:
                            if self.inPuTMsG.startswith('/mq'):
                                for i in range(100):
                                    lag(self.JWT)
                                    await asyncio.sleep(0.00003)
                            if self.inPuTMsG.startswith('/room'):
                                parts = self.inPuTMsG.strip().split()

                                if len(parts) < 3:
                                    message = f"[B][C]{get_random_color()}Use The Command like this : /room uid {xMsGFixinG('password')} !"
                                    P = await self.SEndMsG(self.response.Data.chat_type , message , uid , chat_id , key , iv)
                                    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)

                                uid_room = parts[1].strip()
                                self.room_uid = uid_room
                                password = parts[2].strip()


                                Join = await RedZedJoinRomm(uid_room,password,key,iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine', Join)

                            if self.inPuTMsG.startswith('/leave'):
                                uid_room = self.room_uid
                                leave = await RedZedLeaveRoom(uid_room,key,iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine', leave)

                            if self.inPuTMsG.startswith('/kick'):
                                try:
                                    for i in range(2111):
                                        C = await new_lag(key, iv)
                                        await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , C)
                                        await asyncio.sleep(0.003)
                                    print('finished')
                                except Exception as e:
                                    print(e)
                            if self.inPuTMsG.startswith(("/s5")):
                                try:
                                    dd = chatdata['5']['data']['16']
                                    print('msg in private')
                                    message = f"[B][C]{get_random_color()}\n\nAccepT My InV FasT\n\n"
                                    P = await self.SEndMsG(self.response.Data.chat_type , message , uid , chat_id , key , iv)
                                    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)
                                    PAc = await OpEnSq(key , iv)
                                    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , PAc)





                                    C = await cHSq(5, uid ,key, iv)
                                    await asyncio.sleep(0.5)
                                    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , C)
                                    V = await SEnd_InV(5 , uid , key , iv)
                                    await asyncio.sleep(0.5)
                                    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , V)
                                    E = await ExiT(None , key , iv)
                                    await asyncio.sleep(3)
                                    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , E)
                                except Exception as e:
                                    print('msg in squad' , str(e))


                            if self.inPuTMsG.startswith('/inv'):
                                try:
                                    parts = self.inPuTMsG.strip().split()
                                    uid = int(parts[1])
                                except:
                                    pass
                                V = await SEnd_InV(5 , uid , key , iv)
                                await asyncio.sleep(0.5)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , V)
                            if self.inPuTMsG.startswith('/x/'):
                                CodE = self.inPuTMsG.split('/x/')[1]
                                print(CodE)
                                try:
                                    dd = chatdata['5']['data']['16']
                                    print('msg in private')
                                    EM = await GenJoinSquadsPacket(CodE , key , iv)
                                    joining_team = True
                                    #print(EM , list[key] , list[iv])
                                    await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine' , EM)


                                except Exception as e:
                                    print('msg in squad',str(e))

                            #if self.inPuTMsG.startswith('leave'):
                            #    leave = await ExiT(uid,key,iv)
                            #    await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , leave)
                            #    self.insquad = None

                            if self.inPuTMsG.strip().startswith('/status'):
                                parts = self.inPuTMsG.strip().split()
                                uidINFO = parts[1]
                                if "***" in uidINFO:
                                    uidINFO = uidINFO.replace("***", "106")
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'OnLine' , await SendInFoPaCKeT(uidINFO,key,iv))
                                

                            if self.inPuTMsG.strip().startswith('/s'):
                                EM = await FS(key , iv)
                                await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine' , EM)

                            if self.inPuTMsG.strip().startswith('@a'):

                                try:
                                    dd = chatdata['5']['data']['16']
                                    print('msg in private')
                                    message = f"[B][C]{get_random_color()}\n\nOnLy In SQuaD ! \n\n"
                                    P = await self.SEndMsG(self.response.Data.chat_type, message, uid, uid, key, iv)
                                    await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'ChaT', P)

                                except:
                                    print('msg in squad')

                                    parts = self.inPuTMsG.strip().split()

                                    message = f'[B][C]{get_random_color()}\nACITVE TarGeT -> {xMsGFixinG(uid)}\n'

                                    P = await self.SEndMsG(self.response.Data.chat_type, message, uid, chat_id, key, iv)

                                    uid2 = uid3 = uid4 = uid5 = None
                                    s = False

                                    try:
                                        uid = int(parts[1])
                                        uid2 = int(parts[2])
                                        uid3 = int(parts[3])
                                        uid4 = int(parts[4])
                                        uid5 = int(parts[5])
                                        idT = int(parts[5])

                                    except ValueError as ve:
                                        print("ValueError:", ve)
                                        s = True

                                    except Exception:
                                        idT = len(parts) - 1
                                        idT = int(parts[idT])
                                        print(idT)
                                        print(uid)

                                    if not s:
                                        try:
                                            await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'ChaT', P)

                                            H = await Emote_k(uid, idT, key, iv)
                                            await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine', H)

                                            if uid2:
                                                H = await Emote_k(uid2, idT, key, iv)
                                                await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine', H)
                                            if uid3:
                                                H = await Emote_k(uid3, idT, key, iv)
                                                await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine', H)
                                            if uid4:
                                                H = await Emote_k(uid4, idT, key, iv)
                                                await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine', H)
                                            if uid5:
                                                H = await Emote_k(uid5, idT, key, iv)
                                                await self.SEndPacKeT(self.whisper_writer, self.online_writer, 'OnLine', H)
                                            

                                        except Exception as e:
                                            pass


                            if self.inPuTMsG in ("hi" , "hello" , "fin" , "fen" , "wach", "slm", "cc", "salam"):
                                uid = self.response.Data.uid
                                chat_id = self.response.Data.Chat_ID
                                message = 'Hello Im Dev RedZed\nTelegram : @RedZedKing'
                                P = await self.SEndMsG(self.response.Data.chat_type , message , uid , chat_id , key , iv)
                                await self.SEndPacKeT(self.whisper_writer , self.online_writer , 'ChaT' , P)
                            self.response = None





                if self.whisper_writer is not None:
                    try:
                        self.whisper_writer.close()
                        await self.whisper_writer.wait_closed()
                    except Exception as e:
                        print(f"Error closing whisper_writer: {e}")
                    finally:
                        self.whisper_writer = None

                if self.online_writer is not None:
                    try:
                        self.online_writer.close()
                        await self.online_writer.wait_closed()
                    except Exception as e:
                        print(f"Error closing online_writer: {e}")
                    finally:
                        self.online_writer = None

                self.insquad = None

#
#               self.whisper_writer.close() ; await self.whisper_writer.wait_closed() ; self.whisper_writer = None
#               self.online_writer.close() ; await self.online_writer.wait_closed() ; self.online_writer = None
#               self.insquad = None
                        
                            
                            
            except Exception as e: print(f"ErroR {ip}:{port} - {e}");self.whisper_writer = None
            await asyncio.sleep(reconnect_delay)


    async def restart(self,task1,task2):
        while True:
            if self.online_writer and self.whisper_writer == None:
                await asyncio.gather(task1 , task2)
    async def MaiiiinE(self):
        Uid , Pw = '4733012513','xMaSrY_0L6kklIp_3wt'
        
        open_id , access_token = await GeNeRaTeAccEss(Uid , Pw)

        if not open_id or not access_token: print("ErroR - InvaLid AccounT") ; return None
        
        PyL = await EncRypTMajoRLoGin(open_id , access_token)
        MajoRLoGinResPonsE = await MajorLogin(PyL)
        print(MajoRLoGinResPonsE)
        if not MajoRLoGinResPonsE: print("TarGeT AccounT => BannEd / NoT ReGisTeReD ! ") ; return None
        
        MajoRLoGinauTh = await DecRypTMajoRLoGin(MajoRLoGinResPonsE)
        print(MajoRLoGinauTh)
        UrL = MajoRLoGinauTh.url
        ToKen = MajoRLoGinauTh.token
        print(UrL)
        print(ToKen)
        self.JWT = ToKen
        TarGeT = MajoRLoGinauTh.account_uid
        key = MajoRLoGinauTh.key
        iv = MajoRLoGinauTh.iv
        timestamp = MajoRLoGinauTh.timestamp
        
        LoGinDaTa = await GetLoginData(UrL , PyL , ToKen)
        print(LoGinDaTa)
        if not LoGinDaTa: print("ErroR - GeTinG PorTs From LoGin DaTa !") ; return None
        LoGinDaTaUncRypTinG = await DecRypTLoGinDaTa(LoGinDaTa)
        ReGioN = LoGinDaTaUncRypTinG.Region
        AccountName = LoGinDaTaUncRypTinG.AccountName
        OnLinePorTs = LoGinDaTaUncRypTinG.Online_IP_Port
        ChaTPorTs = LoGinDaTaUncRypTinG.AccountIP_Port
        self.OnLineiP , self.OnLineporT = OnLinePorTs.split(":")
        ChaTiP , ChaTporT = ChaTPorTs.split(":")
        AutHToKen = await xAuThSTarTuP(int(TarGeT) , ToKen , int(timestamp) , key , iv)
        ready_event = asyncio.Event()
        
        task1 = asyncio.create_task(self.TcPChaT(ChaTiP, ChaTporT, AutHToKen,
                                        key, iv, LoGinDaTaUncRypTinG,
                                        ready_event))
        await ready_event.wait()
        await asyncio.sleep(1)
        task2 = asyncio.create_task(self.TcPOnLine(self.OnLineiP , self.OnLineporT , key , iv , AutHToKen))
        #os.system('cls') if os.name == 'nt' else os.system('clear')
        print(render('REDZED', colors=['white', 'red'], align='center'))
        #equipe_emote(ToKen)
        print(f" - SerVeR LoGiN UrL => {login_url} | SerVer Url => {UrL}\n")
        print(f" - GaMe sTaTus > Good | OB => {ob} | Version => {version}\n")
        print(f" - BoT STarTinG And OnLine on TarGet : {AccountName} , UiD : {TarGeT} | ReGioN => {ReGioN}\n")
        print(f" - BoT sTaTus > GooD | OnLinE ! (:\n") 

        await asyncio.gather(task1 , task2)
        await self.restart(self,task1,task2)



client = CLIENT()
async def StarTinG():
    while True:
        try: await asyncio.wait_for(client.MaiiiinE() , timeout = 7 * 60 * 60)
        except asyncio.TimeoutError: print("Token ExpiRed ! , ResTartinG")
        except Exception as e:import traceback; print(f"ErroR TcP - {e} => ResTarTinG ...");traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(StarTinG())