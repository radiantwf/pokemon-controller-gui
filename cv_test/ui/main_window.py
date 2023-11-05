import queue
import threading
import cv2
from PySide6.QtCore import Slot
from PySide6 import QtWidgets, QtGui
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtUiTools import loadUiType
import numpy
from const import ConstClass
from ui.lancher.cv_process import CVProcessLauncher
from ui.qthread.cv_process_display import ProcessedDisplayThread
from ui.lancher.capture import CaptureLauncher

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
        self._processed_display_frames_queue = None
        self._capture_launcher = CaptureLauncher()
        self._cv_process_launcher = CVProcessLauncher()

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        self._display_frame_queue = queue.Queue(1)
        self._recognition_frame_queue = queue.Queue(1)
        self._processed_display_frames_queue = queue.Queue(1)

        self.th_display = CaptureDisplayThread(self, self._display_frame_queue)
        self.th_display.display_frame.connect(self.display_frame)
        self.th_display.start()

        self.th_processed_display = ProcessedDisplayThread(
            self, self._processed_display_frames_queue)
        self.th_processed_display.display_frames.connect(
            self.processed_display_frames)
        self.th_processed_display.start()

        self._capture_launcher.capture_stop()
        self._capture_launcher.capture_start(
            self._display_frame_queue, self._recognition_frame_queue)

        self._cv_process_launcher.cv_process_stop()
        self._cv_process_launcher.cv_process_start(
            self._recognition_frame_queue, self._processed_display_frames_queue)

    def closeEvent(self, event):
        self._cv_process_launcher.cv_process_stop()
        self._capture_launcher.capture_stop()

    def put_frame(self, frame, label):
        np_array = numpy.frombuffer(
            frame.bytes(), dtype=numpy.uint8)
        mat = np_array.reshape(
            (frame.height, frame.width, frame.channels))
        display_mat = cv2.resize(
            mat, (self._my_const.DisplayCameraWidth, self._my_const.DisplayCameraHeight), interpolation=cv2.INTER_AREA)
        display_frame = Frame(display_mat)
        if frame.format == cv2.CAP_PVAPI_PIXELFORMAT_MONO8:
            format = QImage.Format_Grayscale8
        elif frame.format == cv2.CAP_PVAPI_PIXELFORMAT_BGR24:
            format = QImage.Format_BGR888
        else:
            raise ValueError("Unsupported format")
        img = QImage(display_frame.bytes(), display_frame.width, display_frame.height,
                     display_frame.channels*display_frame.width, format)
        # .scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
        pixmap = QPixmap.fromImage(img)
        label.setPixmap(pixmap)

    @Slot(Frame)
    def display_frame(self, frame):
        self.put_frame(frame, self.lblCameraFrame_1)

    @Slot(tuple)
    def processed_display_frames(self, frames):
        frame_2, frame_3, frame_4 = frames
        self.put_frame(frame_2, self.lblCameraFrame_2)
        self.put_frame(frame_3, self.lblCameraFrame_3)
        self.put_frame(frame_4, self.lblCameraFrame_4)
