from io import StringIO
import multiprocessing
import time
import socket
import struct
from PySide6 import QtWidgets
from PySide6.QtWidgets import QMessageBox
from camera.device import VideoDevice
from PySide6.QtCore import Slot,Qt,QEvent,QTimer,QCoreApplication
from PySide6.QtGui import QImage, QPixmap,QPainter
from PySide6.QtMultimedia import QAudioFormat,QAudioSource,QAudioSink,QMediaDevices
from PySide6.QtUiTools import loadUiType
from ui.controller.switch_pro import SwitchProControll
from ui.controller.device import SerialDevice
from ui.qthread.controller import ControllerThread

from ui.qthread.video import VideoThread
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
        self.th_controller = None
        self.th_video = None
        self._key_press_map = dict()
        self._last_sent_action = ""
        self._last_sent_ts = time.monotonic()
        self._current_tag = None
        self._realtime_controller_socket_port = 0

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

        self.th_video = VideoThread(self,self._frame_queue)
        self.th_video.on_recv_frame.connect(self.setImage)
        self.th_video.start()

        self.th_controller = ControllerThread(self)
        self.th_controller.push_action.connect(self.push_action)
        self.th_controller.start()

        self.toolBox.setCurrentIndex(0)
        self.refresh_controller_server()

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


    def closeEvent(self, event):
        self._current_controller.close()
        if self._timer:
            self._timer.stop()
        self.stop_audio()
        if self.th_video:
            self.th_video.stop()
        if self.th_controller:
            self.th_controller.stop()
        if self.th_video:
            self.th_video.wait()
        if self.th_controller:
            self.th_controller.wait()
        event.accept()
        QCoreApplication.instance().aboutToQuit.emit()

    @Slot()
    def on_destroy(self):
        print('on_destroy')

    @Slot(QImage)
    def setImage(self, image):
        if self._current_camera != None:
            pixmap = QPixmap.fromImage(image)#.scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
            self.lblCameraFrame.setPixmap(pixmap)
        else:
            self.lblCameraFrame.clear()

    def refresh_controller_server(self):
        self._realtime_controller_socket_port = 0
        port = self.th_controller.refresh_service()
        if self.toolBox.currentIndex() == 0:
            self._realtime_controller_socket_port = port


    def send_realtime_action_queue(self,action):
        pass

    @Slot(str)
    def push_action(self, action:str):
        self.controller_send_action(action)
        self._set_joystick_labels(action)

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
        if self.cbxSerialList.currentIndex() == 0:
            self._key_press_map.clear()
            self.label_action.setText("")

        if self.cbxSerialList.currentIndex() > 0:
            action = self._get_action_line()
            if action != self._last_sent_action or time.monotonic() - self._last_sent_ts > 5:
                self._last_sent_action = action
                self._last_sent_ts = time.monotonic()
                if self._realtime_controller_socket_port > 0:
                    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    client.sendto(action.encode("utf-8"), ("127.0.0.1", self._realtime_controller_socket_port))
                    client.close()
    
    def _set_joystick_labels(self,action):
        splits = action.upper().split("|", -1)
        buffer = bytearray(7)
        buffer[3] = 0x80
        buffer[4] = 0x80
        buffer[5] = 0x80
        buffer[6] = 0x80
        for s in splits:
            s = s.strip()
            if s == "Y":
                buffer[0] |= 0b1
            elif s == "B":
                buffer[0] |= 0b10
            elif s == "X":
                buffer[0] |= 0b100
            elif s == "A":
                buffer[0] |= 0b1000
            elif s == "L":
                buffer[0] |= 0b10000
            elif s == "R":
                buffer[0] |= 0b100000
            elif s == "ZL":
                buffer[0] |= 0b1000000
            elif s == "ZR":
                buffer[0] |= 0b10000000
            elif s == "MINUS":
                buffer[1] |= 0b1
            elif s == "PLUS":
                buffer[1] |= 0b10
            elif s == "LPRESS":
                buffer[1] |= 0b100
            elif s == "RPRESS":
                buffer[1] |= 0b1000
            elif s == "HOME":
                buffer[1] |= 0b10000
            elif s == "CAPTURE":
                buffer[1] |= 0b100000
            elif s == "TOP":
                buffer[2] |= 0b1
            elif s == "RIGHT":
                buffer[2] |= 0b10
            elif s == "BOTTOM":
                buffer[2] |= 0b100
            elif s == "LEFT":
                buffer[2] |= 0b1000
            elif s == "TOPRIGHT":
                buffer[2] |= 0b0011
            elif s == "BOTTOMRIGHT":
                buffer[2] |= 0b0110
            elif s == "BOTTOMLEFT":
                buffer[2] |= 0b1100
            elif s == "TOPLEFT":
                buffer[2] |= 0b1001
            else:
                stick = s.split("@", -1)
                if len(stick) == 2:
                    x = 0x80
                    y = 0x80
                    coordinate = stick[1].split(",", -1)
                    if len(coordinate) == 2:
                        x = self._coordinate_str_convert_byte(coordinate[0])
                        y = self._coordinate_str_convert_byte(coordinate[1])
                    if stick[0] == "LSTICK":
                            buffer[3] = x
                            buffer[4] = y
                    elif stick[0] == "RSTICK":
                            buffer[5] = x
                            buffer[6] = y

        self._set_label_style(self.label_y,(buffer[0] & 0b1) != 0)
        self._set_label_style(self.label_b,(buffer[0] & 0b10) != 0)
        self._set_label_style(self.label_x,(buffer[0] & 0b100) != 0)
        self._set_label_style(self.label_a,(buffer[0] & 0b1000) != 0)
        self._set_label_style(self.label_l,(buffer[0] & 0b10000) != 0)
        self._set_label_style(self.label_r,(buffer[0] & 0b100000) != 0)
        self._set_label_style(self.label_zl,(buffer[0] & 0b1000000) != 0)
        self._set_label_style(self.label_zr,(buffer[0] & 0b10000000) != 0)

        self._set_label_style(self.label_minus,(buffer[1] & 0b1) != 0)
        self._set_label_style(self.label_plus,(buffer[1] & 0b10) != 0)
        self._set_label_style(self.label_lstick_press,(buffer[1] & 0b100) != 0)
        self._set_label_style(self.label_rstick_press,(buffer[1] & 0b1000) != 0)
        self._set_label_style(self.label_home,(buffer[1] & 0b10000) != 0)
        self._set_label_style(self.label_capture,(buffer[1] & 0b100000) != 0)
        self._set_label_style(self.label_dpad_t,(buffer[2] & 0b1) != 0)
        self._set_label_style(self.label_dpad_r,(buffer[2] & 0b10) != 0)
        self._set_label_style(self.label_dpad_b,(buffer[2] & 0b100) != 0)
        self._set_label_style(self.label_dpad_l,(buffer[2] & 0b1000) != 0)
        self._set_stick_label_style(self.label_lstick_l,(buffer[3] - 0x80) * (-1))
        self._set_stick_label_style(self.label_lstick_r,(buffer[3] - 0x80))
        self._set_stick_label_style(self.label_lstick_t,(buffer[4] - 0x80) * (-1))
        self._set_stick_label_style(self.label_lstick_b,(buffer[4] - 0x80))
        self._set_stick_label_style(self.label_rstick_l,(buffer[5] - 0x80) * (-1))
        self._set_stick_label_style(self.label_rstick_r,(buffer[5] - 0x80))
        self._set_stick_label_style(self.label_rstick_t,(buffer[5] - 0x80) * (-1))
        self._set_stick_label_style(self.label_rstick_b,(buffer[5] - 0x80))
        self.label_action.setText("实时命令：{}".format(action))


    def _coordinate_str_convert_byte(self, str):
        v = 0
        try:
            v = int(float(str))
        except:
            pass
        if v < -128:
            v = -128
        elif v > 127:
            v = 127
        return v + 0x80
    
    def _set_label_style(self,label,pushed):
        if pushed:
            label.setStyleSheet(u"background-color:rgb(0, 0, 255)")
        else:
            label.setStyleSheet(u"background-color:rgb(170, 170, 170)")

    def _set_stick_label_style(self,label,v:int):
        if v>80:
            label.setStyleSheet(u"background-color:rgb(0,0,255)")
        elif v>30:
            label.setStyleSheet(u"background-color:rgb(80,80,255)")
        elif v>2:
            label.setStyleSheet(u"background-color:rgb(140,140,200)")
        else:
            label.setStyleSheet(u"background-color:rgb(170,170,170)")
    
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
    