# coding=utf-8

import websocket, json

def on_open(sock):
    """ 发送请求, 显示进度对话框
    """
    request = {
        "object": "desktop",
        "command": "cache",
        "kwargs": {
            "desktopid": "self.desktopid"
        }
    }
    sock.send(json.dumps(request))
    # sock.close()

def on_message(sock, msg):
    """ 收到消息后更新进度条及详情
    """
    print msg

def on_error(sock, err):
    """ 出错后弹框提示, 然后退出
    """
    print err

def on_close(sock):
    """ 对端关闭后本端没有问题才关闭
    """
    print "socket close %s"%sock

ws = websocket.WebSocketApp("ws://127.0.0.1:9158", on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
ws.run_forever()
