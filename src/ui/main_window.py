
from PySide6 import QtWidgets
from datatype.device import AudioDevice
from PySide6.QtCore import Slot,Qt,QEvent,QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtMultimedia import QAudioFormat,QAudioSource,QAudioSink,QMediaDevices
from PySide6.QtUiTools import loadUiType
Ui_MainWindow, QMainWindowBase = loadUiType("./resources/ui/main_form.ui")

class MainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

    def setupUi(self):
        Ui_MainWindow.setupUi(self,self)
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

    @Slot()
    def button_click(self):
        None

    def play_audio(self):
        if not self._audio_device:
            return
        format_audio = QAudioFormat()
        format_audio.setSampleRate(44100)
        format_audio.setChannelCount(2)
        format_audio.setSampleFormat(QAudioFormat.Int16)

        for dev in QMediaDevices.audioInputs():
            if dev.description() == self._audio_device.name:
                self._audio_input = QAudioSource(dev, format_audio, self)
                self._io_device = self._audio_input.start()
                self._io_device.readyRead.connect(self._readyRead)
                break

        self._output_device = QMediaDevices.defaultAudioOutput()
        self._m_audioSink = QAudioSink(self._output_device, format_audio)
        self._m_output= self._m_audioSink.start()

    @Slot(QImage)
    def setImage1(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    @Slot(QImage)
    def setImage2(self, image):
        pixmap = QPixmap.fromImage(image).scaled(self.label_2.size(), aspectMode=Qt.KeepAspectRatio)
        self.label_2.setPixmap(pixmap)

    @Slot(str)
    def setLog(self, log):
        self.textBrowser.append(log)
        
    @Slot()
    def on_destroy(self):
        self.timer.stop()
        self.th_log.terminate()
        self.th_video.terminate()
        self.th_processed.terminate()
        if self._audio_input != None:
            self._audio_input.stop()
        self._m_audioSink.stop()
        self._frame_queue.close()
    

    @Slot()
    def _readyRead(self):
        data = self._io_device.readAll()
        self._m_output.write(data)
        