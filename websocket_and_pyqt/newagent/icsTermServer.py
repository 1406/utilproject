from SocketServer import BaseRequestHandler, ThreadingTCPServer
import struct, json, hashlib, base64, logging, os, traceback, binascii, random

from ics.framework.message import SendSyncMessage
from ics.framework.util import AES_cryption, AES_decryption, cmd_excute
from ics.framework import ret_code
from ics.framework import environ

LOG = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

def func_ignore(handler, *args, **kwargs):
    ''' 命令字错误的空函数, 函数参数如示例
        建议全部使用kwargs, 而不使用args
    '''
    pass

def login(handler, username=None, password=None):
    try:
        if not username or not password:
            return False

        pswd = hashlib.md5()
        pswd.update(password)

        req = json.loads("{}")
        req["action"] = "login"

        param = json.loads("{}")
        param["username"] = username
        param["password"] = pswd.hexdigest()
        req["param"] = param

        # if admin:
        #     receiver = "manager"
        # else:
        #     receiver = "user"
        # queue = "user" + "__query"
        # result = send_message(receiver, req, retCode=True, queue=queue)
        # 用户登录分3种情况， 1.返回301，登录成功，返回true
        #                     2.返回3024，用户名或密码错误，返回false
        #                     3.其他返回都尝试本地鉴权，抛异常也去本地鉴权
        try:
            response = SendSyncMessage("user", req, queue=None, timeout=60)
        except:
            LOG.error("login except:%s"%traceback.format_exc())
            response = None
        LOG.debug("send_message response:%s" % response)
        if response:
            result = ret_code.Convert(response)
            if result.is_success():
                # 如果服务器鉴权成功, 则保存一个本地鉴权文件
                user_dir = os.path.join(environ.STORAGE_FS_PATH, "users")
                if not os.path.exists(user_dir):
                    cmd_excute('sudo mkdir -p "%s"' % user_dir)
                user_path = os.path.join(user_dir, username)
                encrypt_password = binascii.b2a_hex(AES_cryption("%s %s %s"%(random.randint(0,1000000), pswd.hexdigest(), random.randint(0,1000000))))
                LOG.debug("login success, save local encrypt")
                with open(user_path, "w") as f:
                    f.write(encrypt_password)
                return True
            # 这个else包含登录失败和服务器内部错误等
            else:
                return False
        # 网不通response是空
        else:
            # 尝试本地鉴权，1.若果无本地鉴权文件，鉴权失败返回false
            #               2.本地鉴权成功或失败
            user_path = os.path.join(environ.STORAGE_FS_PATH, "users/%s"%(username))
            if not os.path.exists(user_path):
                return False
            local_passwd = ""
            with open(user_path, "r") as f:
                local_passwd = f.read()

            local_passwd = AES_decryption(binascii.a2b_hex(local_passwd))

            return pswd.hexdigest() == local_passwd.split()[1]
    except:
        LOG.error("login except:%s"%traceback.format_exc())
        return False

task_muster = {
    "user_login": user_login,
    "user_autologin": user_autologin,
    "user_modify_password": user_modify_password,
    "manager_login": manager_login,
    "desktop_query": desktop_query,
    "desktop_cache": desktop_cache,
    "desktop_run": desktop_run,
    "desktop_shutdown": desktop_shutdown,
    "desktop_delete": desktop_delete,
    "desktop_restore": desktop_restore,
    "desktop_create": desktop_create,
    "desktop_display_config": desktop_display_config,
    "desktop_run_default": desktop_run_default,
    "desktop_query_bind": desktop_query_bind,
    "desktop_query_status": desktop_query_status,
    "desktop_poweroff": desktop_poweroff,
    "desktop_poweroff_remote": desktop_poweroff_remote,
    "snapshot_query": snapshot_query,
    "snapshot_create": snapshot_create,
    "snapshot_upload": snapshot_upload,
    "snapshot_restore": snapshot_restore,
    "snapshot_delete": snapshot_delete,
    "snapshot_upload_progress": snapshot_upload_progress,   # 应该去掉, 在上传时实时回传
    "snapshot_clean": snapshot_clean,
    "image_query": image_query,
    "image_create": image_create,
    "image_upload": image_upload,
    "image_modify": image_modify,
    "image_delete": image_delete,
    "host_disk_clean": host_disk_clean,
    "host_disk_is_enough": host_disk_is_enough,
    "host_check_memory_support": host_check_memory_support,
    "host_is_online": host_is_online,
    "host_create": host_create,
    "host_display_change": host_display_change,
    "host_display_info": host_display_info,
    "host_query": host_query,
    "localdisk_query": localdisk_query,
    "localdisk_create": localdisk_create,
    "localdisk_delete": localdisk_delete,
    "localdisk_cleanall": localdisk_cleanall,
    "localdisk_get_disk_space": localdisk_get_disk_space,
    "localdisk_init_block": localdisk_init_block,
    "resolution_get": resolution_get,
    "resolution_set": resolution_set,
    "group_query": group_query,
    "software_query": software_query,
}

class terminal_handler(BaseRequestHandler):
    @property
    def guid(self):
        return "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def handle(self):
        if not self.handshake():
            return

        rcv_buff = ""
        msg_buff = ""

        while True:
            rcv_buff = self.request.recv(128)
            if len(rcv_buff) <= 0:
                continue
            msg_buff += rcv_buff

            msg_len, hdr_len, mask = self.get_len(msg_buff)
            if len(msg_buff) >= msg_len + hdr_len:
                buffstr = self.parse_data(msg_buff)
                print buffstr

                self.excute(buffstr)
                msg_buff = ""
            rcv_buff = ""

    def excute(self, comm_json):
        try:
            req_data = json.loads(comm_json)
            task_muster.get(req_data.command, func_ignore)(self, *req_data.get("args", []), **req_data.get("kwargs", {}))
        except:
            pass

    def handshake(self):
        rcv_buff = self.request.recv(1024)
        print rcv_buff
        if '\r\n\r\n' in rcv_buff:
            headers = {}
            head, body = rcv_buff.split('\r\n\r\n', 1)
            for line in head.split("\r\n")[1:]:
                key, value = line.split(": ", 1)
                headers[key] = value

            headers["Location"] = ("ws://%s%s" % (headers["Host"], '/'))
            key = headers['Sec-WebSocket-Key']
            token = base64.b64encode(hashlib.sha1(str.encode(str(key + self.guid))).digest())

            handshake = "HTTP/1.1 101 Switching Protocols\r\n"\
                "Upgrade: websocket\r\n"\
                "Connection: Upgrade\r\n"\
                "Sec-WebSocket-Accept: " + bytes.decode(token) + "\r\n"\
                "WebSocket-Origin: " + str(headers["Origin"]) + "\r\n"\
                "WebSocket-Location: " + \
                str(headers["Location"]) + "\r\n\r\n"

            self.request.send(str.encode(str(handshake)))

            return True
        else:
            return False


    def get_len(self, msg):
        msglen = ord(msg[1]) & 0x7f
        if msglen == 127:
            msglen = struct.unpack('>Q', str(msg[2:10]))[0]
            hdrlen = 14
            mask = msg[10:14]
        elif msglen == 126:
            msglen = struct.unpack('>H', str(msg[2:4]))[0]
            hdrlen = 8
            mask = msg[4:8]
        else:
            hdrlen = 6
            mask = msg[2:6]

        return msglen, hdrlen, mask

    def parse_data(self, msg):
        msglen, hdrlen, mask = self.get_len(msg)

        rawstr = ""
        i = 0
        for d in msg[hdrlen:]:
            rawstr += chr(ord(d) ^ ord(mask[i % 4]))
            i += 1

        return rawstr

    def send_msg(self, msg):
        msg_utf8 = msg.encode('utf-8')
        datalen = len(msg_utf8)

        if datalen < 125:
            snd_data = struct.pack('>2B', 0x81, datalen)
        elif datalen < 65536:
            snd_data = struct.pack('>2BH', 0x81, 126, datalen)
        elif datalen < 1 << 64:
            snd_data = struct.pack('>2BQ', 0x81, 127, datalen)
        else:
            return

        self.request.send(snd_data + msg_utf8)



if __name__ == "__main__":
    server = ThreadingTCPServer(("127.0.0.1", 9158), terminal_handler)
    server.serve_forever()

