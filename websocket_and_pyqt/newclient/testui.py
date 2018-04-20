# coding=utf-8
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
import sys, signal

class mainwindow(QWidget):
    def __init__(self, parent=None):
        super(mainwindow, self).__init__(parent=parent)
        uic.loadUi("mainwindow.ui", self)

        self.dlg = aboutwidget(self)
        self.dlg.show()
        print self.__dict__
        dict1 = {"aaaaaaa": 1, "bbbbbbb": 2, "cccccc": 3}
        self.__dict__.update(dict1)
        print self.__dict__

    def closeEvent(self, event):
        print 'close event'
        # event.ignore()

class aboutwidget(QDialog):
    def __init__(self, parent=None):
        super(aboutwidget, self).__init__(parent=parent, flags=Qt.FramelessWindowHint)
        uic.loadUi("dialog.ui", self)
        print self.__dict__
        # self.setWindowFlags(Qt.CustomizeWindowHint)

        # wdg = uic.loadUi("aboutwidget.ui")
        wdg = QHBoxLayout(self.scrollAreaWidgetContents)
        wdg.addWidget(QPushButton())
        wdg.addWidget(QToolButton())
        wdg.addWidget(QLabel())
        print wdg.count()
        for i in reversed(range(wdg.count())):
            wdg.removeItem(wdg.itemAt(i))

        print wdg.count()
        # self.scrollArea.setWidget(wdg)
        # bts = QDialogButtonBox.Apply
        # bts |= QDialogButtonBox.Ok
        # wdg.buttonBox.setStandardButtons(bts)

    def wheelEvent(self, event):
        print 'aaa'
        print event.__dict__
        factor = event.angleDelta().y()
        print factor
        self.scrollArea.scrollContentsBy(0, factor/120)

def main():
    # signal.signal(signal.SIGTERM, signal.SIG_IGN)
    # signal.signal(signal.SIGINT, signal.SIG_IGN)

    app = QApplication(sys.argv)
    window = mainwindow()
    with open("./teststyle.qss") as f:
        style = f.read()
        window.setStyleSheet(style)
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
