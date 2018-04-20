# coding=utf-8
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDialog, QHBoxLayout, QPushButton, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
from PyQt5 import uic

from os.path import join as os_path_join

import websocket, json, threading

class dialog(QDialog):
    """ 正文部分为按钮列表的对话框的综合
    """
    def __init__(self, parent=None):
        """ flags传入参数设置对话框为无标题栏
            设置无标题栏有2个枚举值, FramelessWindowHint和CustomizeWindowHint, 尚不知两者区别
            也可使用setWindowFlags()进行设置
        """
        super(dialog, self).__init__(parent=parent, flags=Qt.FramelessWindowHint)
        uic.loadUi("dialog.ui", self)

    def set_tittle(self, title):
        self.lblTitle.setText(title)

    def set_content_buttons(self, btnlist1, btnlist2):
        """ 区域1为特定按钮, 如新增, 删除, 修改, 上传等
            区域2为列表按钮, 如桌面列表, 快照列表, 本地盘列表等
        """
        for btn in btnlist1:
            break

        for btn in btnlist2:
            break

    def set_bottom_buttons(self, dlgbtnlist):
        """ dlgbtnlist为QDialogButtonBox类下枚举数的列表, 如
            QDialogButtonBox.Ok
            QDialogButtonBox.Cancel
            QDialogButtonBox.Apply 等, 详情见
            http://doc.qt.io/archives/qt-4.8/qdialogbuttonbox.html
        """
        btns = 0
        for btn in dlgbtnlist:
            btns |= btn
        self.buttonBox.setStandardButtons(btns)

    def wheelEvent(self, event):
        """ 重写鼠标滚轮事件, 让整个按钮区响应滚轮滚动
            注意界面QScrollArea的widgetResizable要置为False, 或在代码内手动设置
        """
        factor = event.angleDelta().y()
        self.scrollArea.scrollContentsBy(0, factor/120)


class vhostitem(QPushButton):
    """ 这是一个带下拉菜单的按钮
    """
    def __init__(self, vhostdict):
        """ 此处传入的vhlist应该是桌面的vhost.json和desktop.json的合并结果(母盘没有desktop.json)
        """
        super(vhostitem, self).__init__()

        # 将属性加入对象属性中
        # 对象自身作为一个QWidget的派生类, __dict__内数据成员应该都是一些组件, 直接加入不影响原有功能
        self.__dict__.update(vhostdict)

        icon_type = vhostdict.get("os")
        self.setIcon(QIcon(os_path_join("res", icon_type+".png")))

        # 根据传入信息记录3个状态
        ready_flag = True if vhostdict.get("status") == "ready" else False

        run_stat = ""
        run_flag = False
        if vhostdict.get("run_status") == "poweroff":
            pass
        elif vhostdict.get("run_status") == "running":
            run_stat = "(正在运行)"
            run_flag = True
        elif vhostdict.get("run_status") == "snapshot":
            run_stat = "(正在拍摄快照)"
        elif vhostdict.get("run_status") == "syncing":
            run_stat = "(正在同步)"
        elif vhostdict.get("run_status") == "merging":
            run_stat = "(正在合并)"
        else:
            pass

        self.setText(vhostdict.get("name") + run_stat)

        # TODO: 处理下拉菜单
        self.m_menu = QMenu()
        # 处理下拉菜单要区分是桌面还是母盘, 这个属性我们暂定是有前面传进来的
        # XXX: QIcon图标使用QPixmap构造才能自动生成激活\禁用等图像, 用路径构造是到要显示时才加载
        # TODO: 为QAction直接分别绑定事件是否会好一点
        if vhostdict.get("is_image") == "desktop":
            pass
        elif vhostdict.get("is_image") == "image":
            pass
        elif vhostdict.get("is_image") == "image_modify":
            pass
        elif vhostdict.get("is_image") == "image_init":
            pass
        else:
            pass
        self.m_menu.triggered.connect(self.vhost_actions)
        self.setMenu(self.m_menu)

    def triggered_desktop_cache(self):
        """ 发送桌面缓存请求到terminal模块
        """
        # TODO: 先创建一个进度框
        progressdlg = None#progressdialog()
        def on_open(sock):
            """ 发送请求, 显示进度对话框
            """
            request = {
                "object": "desktop",
                "command": "cache",
                "kwargs": {
                    "desktopid": self.desktopid
                }
            }
            sock.send(json.dumps(request))
            progressdlg.show()

        def on_message(sock, msg):
            """ 收到消息后更新进度条及详情
            """
            try:
                msg_dict = json.loads(msg)
            except:
                pass

        def on_error(sock, err):
            """ 出错后弹框提示, 然后退出
            """
            pass
        def on_close(sock):
            """ 对端关闭后本端没有问题才关闭
            """
            pass
        ws = websocket.WebSocketApp("ws://127.0.0.1:9158", on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.run_forever()

    def triggered_desktop_run(self):
        pass

    def triggered_desktop_snapshot(self):
        pass

    def triggered_desktop_display_config(self):
        pass

    def triggered_desktop_localdisk(self):
        pass

    def triggered_desktop_delete(self):
        pass

    def triggered_desktop_shutdown(self):
        pass

    def triggered_desktop_restore(self):
        pass

    def triggered_image_create(self):
        pass

    def triggered_image_modify(self):
        pass

    def triggered_image_run(self):
        pass

    def triggered_image_upload(self):
        pass

    def triggered_image_delete(self):
        pass

    def triggered_image_shutdown(self):
        pass

class mainwindow(QMainWindow):
    def __init__(self, parent=None):
        super(mainwindow, self).__init__(parent=parent)
        uic.loadUi("mainwindow.ui", self)

        # 这个是放置vhost图标的区域
        self.vhost_layout = QHBoxLayout(self.scrollAreaWidgetContents)

        # 控制按钮区绑定点击事件
        self.btnPower.clicked.connect(self.clicked_power)
        self.btnReboot.clicked.connect(self.clicked_reboot)
        self.btnSettings.clicked.connect(self.clicked_settings)
        self.btnLogout.clicked.connect(self.clicked_logout)

        # TODO: 显示OEM

        # TODO: 起定时器刷时间标签

        # TODO: 显示登录框

        # TODO: 起websocket收服务器消息
        # vhost刷新消息/桌面推送消息/agent提示消息/服务器提示信息/服务器快照自动上传(该功能已删除)

    def closeEvent(self, event):
        """ 主窗口屏蔽Alt+F4关闭快捷键
        """
        event.ignore()

    def wheelEvent(self, event):
        """ 重写鼠标滚轮事件, 让整个按钮区响应滚轮滚动
            注意界面QScrollArea的widgetResizable要置为False, 或在代码内手动设置
        """
        factor = event.angleDelta().y()
        self.scrollArea.scrollContentsBy(factor/120, 0)

    def show_vhosts(self, vhlist=()):
        """ 用于显示给定的vhosts
            也可用于清空已显示的vhosts, 此时应传入空列表
            没有定义对应的hide_vhosts方法, 如果要隐藏, 直接用本方法传入空列表删除条目
        """
        # 首先删除所有条目, 反序删除, 防止先删除前面元素导致下标变化
        for i in reversed(range(self.vhost_layout.count())):
            self.vhost_layout.removeItem(self.vhost_layout.itemAt(i))

        if not vhlist:
            return

        # 然后重新生成每个条目
        for vh in vhlist:
            item = vhostitem(vh)
            self.vhost_layout.addWidget(item)   # 此处不能addItem, 类型不兼容

        self.scrollArea.show()

def main():
    app = QApplication([])
    window = mainwindow()
    with open("./style.qss") as f:
        style = f.read()
        window.setStyleSheet(style)
    window.showFullScreen()
    app.exec_()

if __name__ == '__main__':
    main()
