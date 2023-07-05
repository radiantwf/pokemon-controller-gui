import multiprocessing
import sys
import cv2
from PySide6 import QtWidgets
from ui.main_window import MainWindow


def run(camera_control_queue: multiprocessing.Queue, frame_queues):
    app = QtWidgets.QApplication()
    _main_window = MainWindow(camera_control_queue, frame_queues)
    app.installEventFilter(_main_window)
    _main_window.setupUi()
    _main_window.show()
    ret = app.exec_()
    sys.exit(ret)
