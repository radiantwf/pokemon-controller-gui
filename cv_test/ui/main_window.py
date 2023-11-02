import queue
import threading
import cv2
from PySide6.QtCore import Slot
from PySide6 import QtWidgets, QtGui
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtUiTools import loadUiType
import numpy
from const import ConstClass
from ui.lancher.launcher import CameraLauncher

from ui.qthread.capture_display import CaptureDisplayThread
from datatype.frame import Frame
Ui_MainWindow, QMainWindowBase = loadUiType("cv_test/ui/cv_test_form.ui")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self._my_const = ConstClass()
        self._display_frame_queue = None
        self._recognition_frame_queue = None
        self._camera_launcher = CameraLauncher()

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        self._display_frame_queue = queue.Queue(1)
        self._recognition_frame_queue = queue.Queue(1)

        self.th_display = CaptureDisplayThread(self, self._display_frame_queue)
        self.th_display.display_frame.connect(self.display_frame)
        self.th_display.start()

        self._camera_launcher.camera_stop()
        self._camera_launcher.camera_start(self._display_frame_queue, self._recognition_frame_queue)

    def closeEvent(self, event):
        self._camera_launcher.camera_stop()

    @Slot(Frame)
    def display_frame(self, frame):
        np_array = numpy.frombuffer(
            frame.bytes(), dtype=numpy.uint8)
        mat = np_array.reshape(
            (frame.height, frame.width, frame.channels))
        display_mat = cv2.resize(
            mat, (self._my_const.DisplayCameraWidth, self._my_const.DisplayCameraHeight), interpolation=cv2.INTER_AREA)
        display_frame = Frame(self._my_const.DisplayCameraWidth, self._my_const.DisplayCameraHeight,
                              frame.channels, frame.format, display_mat)
        img = QImage(display_frame.bytes(), display_frame.width, display_frame.height,
                     display_frame.channels*display_frame.width, QImage.Format_BGR888)
            # .scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
        pixmap = QPixmap.fromImage(img)
        self.lblCameraFrame_1.setPixmap(pixmap)

