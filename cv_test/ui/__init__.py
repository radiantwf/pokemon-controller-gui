import glob
import os
import sys
from PySide6 import QtWidgets
from ui.main_window import MainWindow


def run():
    app = QtWidgets.QApplication()
    _main_window = MainWindow()
    app.installEventFilter(_main_window)
    _main_window.setupUi()
    _main_window.show()
    ret = app.exec_()
    sys.exit(ret)
