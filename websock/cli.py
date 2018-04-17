import socket

obj = socket.socket()

obj.connect(("127.0.0.1",8080))

ret_bytes = obj.recv(1024)
ret_str = str(ret_bytes)
print(ret_str)

while True:

    inp = raw_input("prompt")
    if inp == "q":
        obj.sendall(str(inp))
        break
    else:
        obj.sendall(str(inp))
        ret_bytes = obj.recv(1024)
        ret_str = str(ret_bytes)
        print(ret_str)