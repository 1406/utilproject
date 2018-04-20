# coding=utf-8

from hashlib import sha1
from base64 import b64encode
from socket import error as SocketError

from SocketServer import ThreadingTCPServer, StreamRequestHandler

import struct, logging, errno

logger = logging.getLogger(__name__)
logging.basicConfig()


class WebsocketHandler(StreamRequestHandler):
    """ websocket frame is like below:
        0               1               2               3
        0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
        +-+-+-+-+-------+-+-------------+-------------------------------+
        |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
        |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
        |N|V|V|V|       |S|             |   (if payload len==126/127)   |
        | |1|2|3|       |K|             |                               |
        +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
        |     Extended payload length continued, if payload len == 127  |
        + - - - - - - - - - - - - - - - +-------------------------------+
        |                               | Masking-key, if MASK set to 1 |
        +-------------------------------+-------------------------------+
        |    Masking-key (continued)    |         Payload Data          |
        +-------------------------------+ - - - - - - - - - - - - - - - +
        :                     Payload Data continued ...                :
        + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
        |                     Payload Data continued ...                |
        +---------------------------------------------------------------+
    """
    def __init__(self, request, client_address, server):
        StreamRequestHandler.__init__(self, request, client_address, server)

    def setup(self):
        StreamRequestHandler.setup(self)

        # 以下掩码不可更改
        self.FIN                = 0x80
        self.OPCODE             = 0x0f
        self.MASKED             = 0x80
        self.PAYLOAD_LEN        = 0x7f
        self.PAYLOAD_LEN_EXT16  = 0x7e
        self.PAYLOAD_LEN_EXT64  = 0x7f

        self.OPCODE_CONTINUATION = 0x0
        self.OPCODE_TEXT         = 0x1
        self.OPCODE_BINARY       = 0x2
        self.OPCODE_CLOSE_CONN   = 0x8
        self.OPCODE_PING         = 0x9
        self.OPCODE_PONG         = 0xA

        self.alive = True

    def handle(self):
        # XXX: 握手操作只进行一次, 不写在循环中
        self.handshake()

        while self.alive:
            self.read_next_message()

    def read_bytes(self, num):
        return map(ord, self.rfile.read(num))

    def read_next_message(self):
        try:
            b1, b2 = self.read_bytes(2)
        except SocketError as e:  # to be replaced with ConnectionResetError for py3
            if e.errno == errno.ECONNRESET:
                logger.info("Client closed connection.")
                print("Error: {}".format(e))
                self.alive = False
                return
            b1, b2 = 0, 0
        except ValueError as e:
            b1, b2 = 0, 0

        fin    = b1 & self.FIN
        opcode = b1 & self.OPCODE
        masked = b2 & self.MASKED
        payload_length = b2 & self.PAYLOAD_LEN

        if not masked:
            logger.warn("Client must always be masked.")
            self.alive = False
            return

        if opcode == self.OPCODE_TEXT:
            opcode_handler = self.server.message_received
        elif opcode == self.OPCODE_PING:
            opcode_handler = self.server.ping_received
        elif opcode == self.OPCODE_PONG:
            opcode_handler = self.server.pong_received
        else:
            if opcode == self.OPCODE_CLOSE_CONN:
                logger.info("Client asked to close connection.")
                self.alive = False
            elif opcode == self.OPCODE_BINARY:
                logger.warn("Binary frames are not supported.")
            elif opcode == self.OPCODE_CONTINUATION:
                logger.warn("Continuation frames are not supported.")
            else:
                logger.warn("Unknown opcode %#x." % opcode)
                self.alive = False
            return

        if payload_length == 126:
            payload_length = struct.unpack(">H", self.rfile.read(2))[0]
        elif payload_length == 127:
            payload_length = struct.unpack(">Q", self.rfile.read(8))[0]

        masks = self.read_bytes(4)
        message_bytes = bytearray()
        for message_byte in self.read_bytes(payload_length):
            message_byte ^= masks[len(message_bytes) % 4]
            message_bytes.append(message_byte)
        opcode_handler(self, message_bytes.decode('utf8'))

    def send_message(self, message):
        self.send_text(message)

    def send_pong(self, message):
        self.send_text(message, self.OPCODE_PONG)

    def send_text(self, message, opcode=0x01):
        """ Important: Fragmented(=continuation) messages are not supported since
            their usage cases are limited - when we don't know the payload length.
        """
        # XXX: 认为传入的消息格式无误, 不进行检查
        # if isinstance(message, bytes):
        #     # this is slower but ensures we have UTF-8
        #     try:
        #         message = message.decode('utf-8')
        #     except UnicodeDecodeError:
        #         return False
        #     if not message:
        #         logger.warning("Can\'t send message, message is not valid UTF-8")
        #         return False
        # elif sys.version_info < (3,0) and (isinstance(message, str) or isinstance(message, unicode)):
        #     pass
        # elif isinstance(message, str):
        #     pass
        # else:
        #     logger.warning('Can\'t send message, message has to be a string or bytes. Given type is %s' % type(message))
        #     return False

        header = bytearray()
        try:
            payload = message.encode('UTF-8')
        except UnicodeEncodeError as e:
            logger.error("Could not encode data to UTF-8 -- %s" % e)
            return False

        header.append(self.FIN | opcode)
        payload_length = len(payload)
        if payload_length <= 125:
            header.append(payload_length)
        elif payload_length < 65536:
            header.append(self.PAYLOAD_LEN_EXT16)
            header.extend(struct.pack(">H", payload_length))
        elif payload_length < 18446744073709551616:
            header.append(self.PAYLOAD_LEN_EXT64)
            header.extend(struct.pack(">Q", payload_length))
        else:
            raise Exception("Message is too big. Consider breaking it into chunks.")

        self.request.send(header + payload)

    def read_http_headers(self):
        headers = {}
        # first line should be HTTP GET
        http_get = self.rfile.readline().decode().strip()
        assert http_get.upper().startswith('GET')
        # remaining should be headers
        while True:
            header = self.rfile.readline().decode().strip()
            if not header:
                break
            head, value = header.split(':', 1)
            headers[head.lower().strip()] = value.strip()
        return headers

    def handshake(self):
        headers = self.read_http_headers()

        try:
            assert headers['upgrade'].lower() == 'websocket'

            key = headers['sec-websocket-key']

            response = self.make_handshake_response(key)
            if self.request.send(response.encode()):
                self.server.client_handshaken(self)

        except AssertionError:
            logger.warning("Client upgrade portocal error")
            self.alive = False

        except KeyError:
            logger.warning("Client tried to connect but was missing a key")
            self.alive = False

    def make_handshake_response(self, key):
        GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        hash = sha1(key.encode() + GUID.encode())
        response_key = b64encode(hash.digest()).strip()

        return  'HTTP/1.1 101 Switching Protocols\r\n'\
                'Upgrade: websocket\r\n'              \
                'Connection: Upgrade\r\n'             \
                'Sec-WebSocket-Accept: %s\r\n'        \
                '\r\n' % response_key.decode('ASCII')

    def finish(self):
        self.server.client_finish(self)


class WebsocketServer(ThreadingTCPServer):
    """ A websocket server waiting for clients to connect.
    """
    def __init__(self, server_address, **kwargs):
        """ kwargs可进行扩展, 如有需要再实现
        """
        ThreadingTCPServer.__init__(self, server_address, WebsocketHandler)

        self.on_client_handshaken = kwargs.get("on_client_handshaken")
        self.on_message_received = kwargs.get("on_message_received")
        self.on_client_finish = kwargs.get("on_client_finish")

        self.clients = []

    def message_received(self, handler, msg):
        if self.on_message_received is not None:
            self.on_message_received(handler, self, msg)

    def ping_received(self, handler, msg):
        handler.send_pong(msg)

    def pong_received(self, handler, msg):
        pass

    def client_handshaken(self, handler):
        self.clients.append(handler)

        if self.on_client_handshaken is not None:
            self.on_client_handshaken(handler, self)

    def client_finish(self, handler):
        if handler in self.clients:
            if self.on_client_finish is not None:
                self.on_client_finish(handler, self)

            self.clients.remove(handler)

    def send_message(self, handler, msg):
        handler.send_message(msg)

    def send_all(self, msg):
        for client in self.clients:
            self.send_message(client, msg)


if __name__ == "__main__":
    def on_client_handshaken(client, server):
        print "client up line "
        print server.clients
        print vars(client).items()
    def on_message_received(client, server, message):
        print "receive message %s"%message
        print client.client_address
        client.request.close()
    def on_client_finish(client, server):
        print "client down line "
    srv = WebsocketServer(("127.0.0.1", 9158), on_client_handshaken=on_client_handshaken, on_message_received=on_message_received, on_client_finish=on_client_finish)
    srv.serve_forever()
