import glob
import os
import sys
from PySide6 import QtWidgets
from ui.main_window import MainWindow


def run():
    files_to_delete = glob.glob('/tmp/poke_ui_*.sock')
    for file in files_to_delete:
        os.remove(file)

    app = QtWidgets.QApplication()
    _main_window = MainWindow()
    app.installEventFilter(_main_window)
    _main_window.setupUi()
    _main_window.show()
    ret = app.exec_()
    sys.exit(ret)
