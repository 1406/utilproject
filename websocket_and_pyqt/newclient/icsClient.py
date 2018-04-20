# coding=utf-8
import threading

import gui


if __name__ == '__main__':
    threading.Thread(target=gui.main).start()