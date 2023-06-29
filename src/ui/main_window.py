from io import StringIO
import multiprocessing
import time
from PySide6 import QtWidgets
from PySide6.QtWidgets import QMessageBox
from camera.device import VideoDevice
from PySide6.QtCore import Slot,Qt,QEvent,QTimer
from PySide6.QtGui import QImage, QPixmap,QPainter
from PySide6.QtMultimedia import QAudioFormat,QAudioSource,QAudioSink,QMediaDevices
from PySide6.QtUiTools import loadUiType
from controller.device import SerialDevice
from controller.switch_pro import SwitchProControll

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

        self._timer = None
        self._m_audioSink = None
        self._audio_input = None
        self._cameras = []
        self._serial_devices = []
        self._current_camera = None
        self._current_controller = SwitchProControll()
        self.th_processed = None
        self._key_press_map = dict()
        self._last_sent_action = ""
        self._last_sent_ts = time.monotonic()
        self._current_tag = None

    def setupUi(self):
        Ui_MainWindow.setupUi(self,self)
        self.build_camera_list_comboBox()
        self.build_audio_list_comboBox()
        self.build_serial_device_list_comboBox()
        self.destroyed.connect(self.on_destroy)
        self.chkMute.stateChanged.connect(self.on_mute_changed)
        self.btnCapture.clicked.connect(self.on_capture_clicked)
        self.btnRescan.clicked.connect(self.on_rescan_clicked)
        self.btnSerialRescan.clicked.connect(self.on_serial_rescan_clicked)

        self.th_processed = VideoThread(self)
        self.th_processed.set_input(self._frame_queue)
        self.th_processed.video_frame.connect(self.setImage)
        self.th_processed.start()
        self._timer = QTimer()
        self._timer.timeout.connect(self.key_send)
        self._timer.start(1)

    def build_serial_device_list_comboBox(self):
        try:
            self.cbxSerialList.currentIndexChanged.disconnect(self.on_serial_changed)
        except:
            None
        self.cbxSerialList.clear()

        self._serial_devices = SerialDevice.list_device()
        devices = []
        devices.append("选择NS控制设备")
        for device in self._serial_devices:
            devices.append(device.name)

        self.cbxSerialList.addItems(devices)
        self.cbxSerialList.setCurrentIndex(0)
        self.cbxSerialList.currentIndexChanged.connect(self.on_serial_changed)
        self.on_serial_changed()

    def build_camera_list_comboBox(self):
        try:
            self.cbxCameraList.currentIndexChanged.disconnect(self.on_camera_changed)
        except:
            None
        self.cbxCameraList.clear()
        self._cameras = VideoDevice.list_device()
        cameras = []
        cameras.append("选择视频输入设备")
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

    def build_audio_list_comboBox(self):
        try:
            self.cbxAudioList.currentIndexChanged.disconnect(self.on_audio_changed)
        except:
            None
        self.cbxAudioList.clear()
        audios = []
        audios.append("选择音频输入设备")
        for audio_info in QMediaDevices.audioInputs():
            audios.append(audio_info.description())
        self.cbxAudioList.addItems(audios)
        self.cbxAudioList.setCurrentIndex(0)
        self.cbxAudioList.currentIndexChanged.connect(self.on_audio_changed)
        self.on_audio_changed()

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
    
    def on_serial_changed(self):
        self._current_controller.close()
        if self.cbxSerialList.currentIndex() == 0:
            return
        ret = self._current_controller.open(self._serial_devices[self.cbxSerialList.currentIndex() - 1])
        if not ret:
            self.pop_switch_pro_controller_err_dialog()
        
    def pop_switch_pro_controller_err_dialog(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText("NS控制设备连接错误")
        msg_box.setInformativeText("请检查设备连接或选择其他设备")
        msg_box.setWindowTitle("错误")
        msg_box.exec_()
        self.cbxSerialList.setCurrentIndex(0)

    def controller_send_action(self,action:str):
        try:
            self._current_controller.send_action(action+"\n")
        except:
            self.pop_switch_pro_controller_err_dialog()

        

    def on_capture_clicked(self):
        self._camera_control_queue.put_nowait("camera")

    def on_rescan_clicked(self):
        self.build_camera_list_comboBox()
        self.build_audio_list_comboBox()

    def on_serial_rescan_clicked(self):
        self.build_serial_device_list_comboBox()


    @Slot()
    def _readyRead(self):
        data = self._io_device.readAll()
        self._m_output.write(data)

    @Slot()
    def on_destroy(self):
        self._current_controller.close()
        if self._timer != None:
            self._timer.stop()
        self.stop_audio()
        if self.th_processed != None:
            self.th_processed.terminate()

    @Slot(QImage)
    def setImage(self, image):
        if self._current_camera != None:
            pixmap = QPixmap.fromImage(image)#.scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
            self.lblCameraFrame.setPixmap(pixmap)
        else:
            self.lblCameraFrame.clear()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            self._key_press_map[event.key()] = time.monotonic()
        elif event.type() == QEvent.Type.KeyRelease:
            self._key_press_map.pop(event.key(),None)
        elif event.type() == QEvent.Type.FocusOut:
            self._key_press_map.clear()

        count = 0
        if self._key_press_map.get(Qt.Key_A):
            count += 1
        if self._key_press_map.get(Qt.Key_S):
            count += 1
        if self._key_press_map.get(Qt.Key_D):
            count += 1
        if self._key_press_map.get(Qt.Key_W):
            count += 1
        if count > 2:
            self._key_press_map.pop(Qt.Key_A,None)
            self._key_press_map.pop(Qt.Key_S,None)
            self._key_press_map.pop(Qt.Key_D,None)
            self._key_press_map.pop(Qt.Key_W,None)
        if self._key_press_map.get(Qt.Key_A) and self._key_press_map.get(Qt.Key_D):
            self._key_press_map.pop(Qt.Key_A,None)
            self._key_press_map.pop(Qt.Key_D,None)
        if self._key_press_map.get(Qt.Key_S) and self._key_press_map.get(Qt.Key_W):
            self._key_press_map.pop(Qt.Key_S,None)
            self._key_press_map.pop(Qt.Key_W,None)
        
        count = 0
        if self._key_press_map.get(Qt.Key_Semicolon):
            count += 1
        if self._key_press_map.get(Qt.Key_Comma):
            count += 1
        if self._key_press_map.get(Qt.Key_Period):
            count += 1
        if self._key_press_map.get(Qt.Key_Slash):
            count += 1
        if count > 2:
            self._key_press_map.pop(Qt.Key_Semicolon,None)
            self._key_press_map.pop(Qt.Key_Comma,None)
            self._key_press_map.pop(Qt.Key_Period,None)
            self._key_press_map.pop(Qt.Key_Slash,None)
        if self._key_press_map.get(Qt.Key_Semicolon) and self._key_press_map.get(Qt.Key_Period):
            self._key_press_map.pop(Qt.Key_Semicolon,None)
            self._key_press_map.pop(Qt.Key_Period,None)
        if self._key_press_map.get(Qt.Key_Period) and self._key_press_map.get(Qt.Key_Slash):
            self._key_press_map.pop(Qt.Key_Period,None)
            self._key_press_map.pop(Qt.Key_Slash,None)

        count = 0
        if self._key_press_map.get(Qt.Key_F):
            count += 1
        if self._key_press_map.get(Qt.Key_C):
            count += 1
        if self._key_press_map.get(Qt.Key_V):
            count += 1
        if self._key_press_map.get(Qt.Key_B):
            count += 1
        if count > 1:
            self._key_press_map.pop(Qt.Key_F,None)
            self._key_press_map.pop(Qt.Key_C,None)
            self._key_press_map.pop(Qt.Key_V,None)
            self._key_press_map.pop(Qt.Key_B,None)
        if self._key_press_map.get(Qt.Key_F) and self._key_press_map.get(Qt.Key_V):
            self._key_press_map.pop(Qt.Key_F,None)
            self._key_press_map.pop(Qt.Key_V,None)
        if self._key_press_map.get(Qt.Key_C) and self._key_press_map.get(Qt.Key_B):
            self._key_press_map.pop(Qt.Key_C,None)
            self._key_press_map.pop(Qt.Key_B,None)
        return QtWidgets.QMainWindow.eventFilter(self, obj, event)

    def key_send(self):
        if self.tabWidget.currentIndex() != 0 or self.cbxSerialList.currentIndex() == 0:
            self._key_press_map.clear()
            self.label_action.setText("")

        self._set_joystick_label(Qt.Key_A,self.label_a)
        self._set_joystick_label(Qt.Key_W,self.label_w)
        self._set_joystick_label(Qt.Key_S,self.label_s)
        self._set_joystick_label(Qt.Key_D,self.label_d)
        self._set_joystick_label(Qt.Key_X,self.label_x)

        self._set_joystick_label(Qt.Key_Semicolon,self.label_rt)
        self._set_joystick_label(Qt.Key_Comma,self.label_rl)
        self._set_joystick_label(Qt.Key_Period,self.label_rb)
        self._set_joystick_label(Qt.Key_Slash,self.label_rr)
        self._set_joystick_label(Qt.Key_Apostrophe,self.label_rc)

        self._set_joystick_label(Qt.Key_F,self.label_f)
        self._set_joystick_label(Qt.Key_C,self.label_c)
        self._set_joystick_label(Qt.Key_B,self.label_b)
        self._set_joystick_label(Qt.Key_V,self.label_v)

        self._set_joystick_label(Qt.Key_R,self.label_r)
        self._set_joystick_label(Qt.Key_Y,self.label_y)
        self._set_joystick_label(Qt.Key_G,self.label_g)
        self._set_joystick_label(Qt.Key_H,self.label_h)

        self._set_joystick_label(Qt.Key_Q,self.label_q)
        self._set_joystick_label(Qt.Key_E,self.label_e)
        self._set_joystick_label(Qt.Key_O,self.label_o)
        self._set_joystick_label(Qt.Key_U,self.label_u)

        self._set_joystick_label(Qt.Key_I,self.label_i)
        self._set_joystick_label(Qt.Key_J,self.label_j)
        self._set_joystick_label(Qt.Key_L,self.label_l)
        self._set_joystick_label(Qt.Key_K,self.label_k)

        if self.tabWidget.currentIndex() == 0 and self.cbxSerialList.currentIndex() > 0:
            action = self._get_action_line()
            if action != self._last_sent_action or time.monotonic() - self._last_sent_ts > 5:
                self._last_sent_action = action
                self._last_sent_ts = time.monotonic()
                self.label_action.setText("实时命令：{}".format(action))
                self.controller_send_action(action)
                    # self._controller_action_queue.put_nowait(macro.Realtime(action))
        self.repaint()
    
    def _set_joystick_label(self,key,label):
        if self._key_press_map.get(key) != None:
            label.setStyleSheet(u"background-color:rgb(0, 0, 255)")
        else:
            label.setStyleSheet(u"background-color:rgb(170, 170, 170)")
    
    def _get_action_line(self)->str:
        sio = StringIO()
        if self._key_press_map.get(Qt.Key_L):
            sio.write("A|")
        if self._key_press_map.get(Qt.Key_K):
            sio.write("B|")
        if self._key_press_map.get(Qt.Key_I):
            sio.write("X|")
        if self._key_press_map.get(Qt.Key_J):
            sio.write("Y|")
            
        if self._key_press_map.get(Qt.Key_E):
            sio.write("L|")
        if self._key_press_map.get(Qt.Key_Q):
            sio.write("ZL|")
        if self._key_press_map.get(Qt.Key_U):
            sio.write("R|")
        if self._key_press_map.get(Qt.Key_O):
            sio.write("ZR|")

        if self._key_press_map.get(Qt.Key_R):
            sio.write("MINUS|")
        if self._key_press_map.get(Qt.Key_Y):
            sio.write("PLUS|")
        if self._key_press_map.get(Qt.Key_G):
            sio.write("CAPTURE|")
        if self._key_press_map.get(Qt.Key_H):
            sio.write("HOME|")

        if self._key_press_map.get(Qt.Key_F):
            sio.write("TOP|")
        if self._key_press_map.get(Qt.Key_C):
            sio.write("LEFT|")
        if self._key_press_map.get(Qt.Key_V):
            sio.write("BOTTOM|")
        if self._key_press_map.get(Qt.Key_B):
            sio.write("RIGHT|")
        
        if self._key_press_map.get(Qt.Key_X):
            sio.write("LPRESS|")
        if self._key_press_map.get(Qt.Key_Apostrophe):
            sio.write("RPRESS|")
        x = 0
        y = 0
        if self._key_press_map.get(Qt.Key_W):
            y = -127
        elif self._key_press_map.get(Qt.Key_S):
            y = 127
        if self._key_press_map.get(Qt.Key_D):
            x = 127
        elif self._key_press_map.get(Qt.Key_A):
            x = -127
        if x != 0 or y !=0:
            sio.write("LSTICK@{},{}|".format(x,y))
        x = 0
        y = 0
        if self._key_press_map.get(Qt.Key_Semicolon):
            y = -127
        elif self._key_press_map.get(Qt.Key_Period):
            y = 127
        if self._key_press_map.get(Qt.Key_Period):
            x = 127
        elif self._key_press_map.get(Qt.Key_Comma):
            x = -127
        if x != 0 or y !=0:
            sio.write("RSTICK@{},{}|".format(x,y))
        sio.flush()
        action = sio.getvalue()
        sio.close()
        return action
    