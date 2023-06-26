import sys
import cv2
from PySide6.QtUiTools import loadUiType
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtMultimedia import QMediaDevices

Ui_MainWindow, QMainWindowBase = loadUiType("./resources/ui/main_form.ui")
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.search_cameras()
        self.search_audios()

    def search_cameras(self):
        cameras = []
        cameras.append("无设备")
        for camera_info in QMediaDevices.videoInputs():
            cameras.append(camera_info.description())
        self.cbxCameraList.addItems(cameras)

    def search_audios(self):
        audios = []
        audios.append("无设备")
        for audio_info in QMediaDevices.audioInputs():
            audios.append(audio_info.description())
        self.cbxAudioList.addItems(audios)

def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
