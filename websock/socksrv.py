import SocketServer


class Myserver(SocketServer.BaseRequestHandler):

    def handle(self):

        conn = self.request
        print(self.request)
        conn.send(bytes("你好，我是机器人"))
        while True:
            ret_bytes = conn.recv(1024)
            ret_str = str(ret_bytes)
            print(ret_str)
            if ret_str == "q":
                break
            conn.send(bytes(ret_str+"你好我好大家好"))


if __name__ == "__main__":
    server = SocketServer.ThreadingTCPServer(("127.0.0.1", 8080), Myserver)
    server.serve_forever()
