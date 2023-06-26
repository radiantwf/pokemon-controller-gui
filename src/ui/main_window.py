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
        self._m_audioSink = None
        self._audio_input = None
        self._mute_flag = False

    def setupUi(self):
        Ui_MainWindow.setupUi(self,self)
        self.search_cameras()
        self.search_audios()
        self.destroyed.connect(self.on_destroy)
        self.cbxAudioList.currentIndexChanged.connect(self.on_audio_changed)
        self.chkMute.stateChanged.connect(self.on_mute_changed)

    def on_mute_changed(self):
        if self.chkMute.isChecked():
            self._mute_flag = True
        else:
            self._mute_flag = False
    
    def on_audio_changed(self):
        self.play_audio()

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

    def play_audio(self):
        self.stop_audio()
        if self.cbxAudioList.currentIndex == 0:
            return
        format_audio = QAudioFormat()
        format_audio.setSampleRate(44100)
        format_audio.setChannelCount(2)
        format_audio.setSampleFormat(QAudioFormat.Int16)

        for dev in QMediaDevices.audioInputs():
            if dev.description() == self.cbxAudioList.currentText():
                self._audio_input = QAudioSource(dev, format_audio, self)
                self._io_device = self._audio_input.start()
                self._io_device.readyRead.connect(self._readyRead)
                break

        self._output_device = QMediaDevices.defaultAudioOutput()
        self._m_audioSink = QAudioSink(self._output_device, format_audio)
        self._m_output= self._m_audioSink.start()

    def stop_audio(self):
        if self._audio_input != None:
            self._audio_input.stop()
            self._audio_input = None
        if self._m_audioSink != None:
            self._m_audioSink.stop()
            self._m_audioSink = None
        
    @Slot()
    def _readyRead(self):
        if self._mute_flag:
            return
        data = self._io_device.readAll()
        self._m_output.write(data)

    @Slot()
    def on_destroy(self):
        self.stop_audio()
