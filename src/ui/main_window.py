import multiprocessing
from PySide6 import QtWidgets
from capture.device import VideoDevice
from PySide6.QtCore import Slot,Qt,QEvent,QTimer
from PySide6.QtGui import QImage, QPixmap,QPainter
from PySide6.QtMultimedia import QAudioFormat,QAudioSource,QAudioSink,QMediaDevices
from PySide6.QtUiTools import loadUiType

from ui.video import VideoThread
Ui_MainWindow, QMainWindowBase = loadUiType("./resources/ui/main_form.ui")

class MainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self,camera_control_queue:multiprocessing.Queue,frame_queues):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        
        # 摄像头控制命令队列
        self._camera_control_queue = camera_control_queue

        # 图像采集桢管道集合
        self._frame_queue = frame_queues[1]
        # self._processed_frame_queue = frame_queues[2]

        self._m_audioSink = None
        self._audio_input = None
        self._cameras = []
        self._current_camera = None
        self.th_processed = None

    def setupUi(self):
        Ui_MainWindow.setupUi(self,self)
        self.build_camera_list_comboBox()
        self.search_audios()
        self.destroyed.connect(self.on_destroy)
        self.cbxAudioList.currentIndexChanged.connect(self.on_audio_changed)
        self.chkMute.stateChanged.connect(self.on_mute_changed)

        self.th_processed = VideoThread(self)
        self.th_processed.set_input(self._frame_queue)
        self.th_processed.video_frame.connect(self.setImage)
        self.th_processed.start()

    def build_camera_list_comboBox(self):
        try:
            self.cbxCameraList.currentIndexChanged.disconnect(self.on_camera_changed)
        except:
            None
        self.cbxCameraList.clear()
        self._cameras = VideoDevice.list_device()
        cameras = []
        cameras.append("无设备")
        for camera_info in self._cameras:
            cameras.append(camera_info.name)
        self.cbxCameraList.addItems(cameras)
        self.cbxCameraList.setCurrentIndex(0)
        self.cbxCameraList.currentIndexChanged.connect(self.on_camera_changed)
        self.on_camera_changed()

    def build_fps_comboBox(self):
        try:
            self.cbxFps.currentIndexChanged.disconnect(self.on_fps_changed)
        except:
            None
        self.cbxFps.clear()
        if self._current_camera == None:
            minFps = 0
            maxFps = 0
        else:
            minFps = round(self._current_camera.min_fps)
            maxFps = round(self._current_camera.max_fps)
        fps = []
        cbxText = ""
        for f in [5,10,15,30,60]:
            if f < minFps:
                continue
            if f == maxFps:
                cbxText = str(f)
                fps.append(cbxText)
                break
            if f > maxFps: 
                cbxText = str(maxFps)
                fps.append(str(maxFps))
                break
            if f < maxFps: 
                cbxText = str(f)
                fps.append(cbxText)
        self.cbxFps.addItems(fps)
        self.cbxFps.setCurrentText(cbxText)
        self.cbxFps.currentIndexChanged.connect(self.on_fps_changed)
        self.on_fps_changed()

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
        if self.chkMute.isChecked():
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
        
    def on_camera_changed(self):
        if self.cbxCameraList.currentIndex() == 0:
            self._current_camera = None
        else:
            self._current_camera = self._cameras[self.cbxCameraList.currentIndex() - 1]
        self.build_fps_comboBox()

    def on_fps_changed(self):
        if self._current_camera != None:
            self._current_camera.setFps(int(self.cbxFps.currentText()))
        self._camera_control_queue.put_nowait(self._current_camera)

    def on_mute_changed(self):
        self.play_audio()
    
    def on_audio_changed(self):
        self.play_audio()

    @Slot()
    def _readyRead(self):
        data = self._io_device.readAll()
        self._m_output.write(data)

    @Slot()
    def on_destroy(self):
        self.stop_audio()
        if self.th_processed != None:
            self.th_processed.terminate()

    @Slot(QImage)
    def setImage(self, image):
        pixmap = QPixmap.fromImage(image)#.scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
        self.lblCameraFrame.setPixmap(pixmap)