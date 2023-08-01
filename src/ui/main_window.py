import datetime
import math
import multiprocessing
import os
import queue
import time
import cv2
import numpy
import pygame
from const import ConstClass
from PySide6 import QtWidgets
from PySide6.QtWidgets import QMessageBox, QLabel, QListWidgetItem
from camera.device import CameraDevice
from PySide6.QtCore import Slot, Qt, QEvent, QTimer, QCoreApplication
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QAudioSink, QMediaDevices
from PySide6.QtUiTools import loadUiType
from datatype.frame import Frame
from log import send_log
from ui.camera.launcher import CameraLauncher
from ui.controller.launcher import ControllerLauncher
from ui.qthread.action_display import ActionDisplayThread
from ui.qthread.display import DisplayThread
from ui.qthread.log import LogThread
from datatype.input import ControllerInput, InputEnum, StickEnum
from ui.joystick.device import JoystickDevice
from ui.joystick.joystick import Joystick
from ui.macro.dialog import LaunchMacroParasDialog
from ui.macro.launcher import MacroLauncher

from ui.qthread.video import VideoThread
Ui_MainWindow, QMainWindowBase = loadUiType("./resources/ui/main_form.ui")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        # 控制器输入命令队列
        self._controller_input_action_queue:multiprocessing.Queue = None

        pygame.init()
        pygame.joystick.init()
        JoystickDevice.list_device()
        self._my_const = ConstClass()
        self._timer = None
        self._joystick_timer = None
        self._m_audioSink = None
        self._audio_input = None
        self._cameras = []
        self._joystick_devices = []
        self._serial_devices = []
        self._current_joystick = None
        self._current_camera = None
        self.th_video = None
        self.th_log = None
        self.th_action_display = None
        self._display_frame_queue = None
        self.th_display = None
        self._capture = False

        # self._joystick_timer = None
        self._key_press_map = dict()
        self._last_sent_ts = time.monotonic()
        self._current_controller_input_joystick: ControllerInput = None
        self._current_controller_input_keyboard: ControllerInput = None
        self._last_sent_input = ControllerInput()

        start_color = (170, 170, 170)
        end_color = (0, 0, 255)
        steps = 1001
        self._stick_label_gradient_colors = self._gradient(
            start_color, end_color, steps)
        self._macro_list = []
        self._macro_launcher = MacroLauncher()
        self._controller_launcher = ControllerLauncher()
        self._camera_launcher = CameraLauncher()

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        self.build_camera_list_comboBox()
        self.build_audio_list_comboBox()
        self.build_serial_device_list_comboBox()
        self.build_joystick_device_list_comboBox()
        self.destroyed.connect(self.on_destroy)
        self.chkMute.stateChanged.connect(self.on_mute_changed)
        self.toolBox.currentChanged.connect(self.on_toolBox_current_changed)
        self.btnCapture.clicked.connect(self.on_capture_clicked)
        self.btnRescan.clicked.connect(self.on_rescan_clicked)
        self.btnSerialRescan.clicked.connect(self.on_serial_rescan_clicked)
        self.btnJoystickRescan.clicked.connect(self.on_joystick_rescan_clicked)

        self.th_log = LogThread(self)
        self.th_log.log.connect(self.setLog)
        self.th_log.start()
        self._display_frame_queue = queue.Queue(1)
        self.th_display = DisplayThread(self, self._display_frame_queue)
        self.th_display.display_frame.connect(self.display_frame)
        self.th_display.start()
        
        self.th_action_display = ActionDisplayThread(self)
        self.th_action_display.action.connect(self.displayAction)
        self.th_action_display.start()

        self.chkJoystickButtonSwitch.stateChanged.connect(
            self.on_joystick_button_switch_changed)

        self.toolBox.setCurrentIndex(0)

        self._timer = QTimer()
        self._timer.timeout.connect(self.realtime_control_action_send)
        self._timer.start(1)

        self.build_macro_list_listView()
        self.btn_macro_opt.clicked.connect(self.macro_opt)
        self.btn_macro_refresh.clicked.connect(self.macro_refresh)
        

    def build_serial_device_list_comboBox(self):
        try:
            self.cbxSerialList.currentIndexChanged.disconnect(
                self.on_serial_changed)
        except:
            None
        self.cbxSerialList.clear()

        self._serial_devices = self._controller_launcher.list_controller()
        devices = []
        devices.append("选择NS控制设备")
        for device in self._serial_devices:
            devices.append(device.name)

        self.cbxSerialList.addItems(devices)
        self.cbxSerialList.setCurrentIndex(0)
        self.cbxSerialList.currentIndexChanged.connect(self.on_serial_changed)
        self.on_serial_changed()

    def build_joystick_device_list_comboBox(self):
        try:
            self.cbxJoystickList.currentIndexChanged.disconnect(
                self.on_joystick_changed)
        except:
            None
        self.cbxJoystickList.clear()
        self._joystick_devices = JoystickDevice.list_device()
        devices = []
        devices.append("选择本地控制手柄")
        for device in self._joystick_devices:
            devices.append(device.name)

        self.cbxJoystickList.addItems(devices)
        self.cbxJoystickList.setCurrentIndex(0)
        self.cbxJoystickList.currentIndexChanged.connect(
            self.on_joystick_changed)
        self.on_joystick_changed()

    def build_camera_list_comboBox(self):
        try:
            self.cbxCameraList.currentIndexChanged.disconnect(
                self.on_camera_changed)
        except:
            None
        self.cbxCameraList.clear()
        self._cameras = CameraDevice.list_device()
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
        for f in [5, 10, 15, 30, 60]:
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
            self.cbxAudioList.currentIndexChanged.disconnect(
                self.on_audio_changed)
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

    def build_macro_list_listView(self):
        self._macro_list = self._macro_launcher.list_macro()
        self.listWidget_macro.clear()
        for macro in self._macro_list:
            item = QListWidgetItem(macro["summary"])
            self.listWidget_macro.addItem(item)
            
    def macro_opt(self):
        if self.listWidget_macro.currentRow() < 0:
            return
        if not self.check_macro_thread_running():
            return
        
        self.on_serial_changed()

        if not self._controller_input_action_queue:
            return
        macro = self._macro_list[self.listWidget_macro.currentRow()]
        dialog = LaunchMacroParasDialog(self,macro)
        ret = dialog.exec_()
        if ret == QtWidgets.QDialog.Accepted:
            script = dialog.get_macro_script()
            paras = dict()
            for para in script["paras"]:
                paras[para["name"]] = para["value"]
            self._macro_launcher.macro_start(script["name"], self._controller_input_action_queue, script["loop"], paras)

    def macro_refresh(self):
        self.build_macro_list_listView()

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
        self._m_output = self._m_audioSink.start()

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
            self._current_camera = self._cameras[self.cbxCameraList.currentIndex(
            ) - 1]
        self.build_fps_comboBox()

    def on_fps_changed(self):
        if self._current_camera != None:
            self._current_camera.setFps(int(self.cbxFps.currentText()))
        self._camera_launcher.camera_stop()
        if self.th_video:
            self.th_video.stop()
            if not self.th_video.wait(1000):
                self.th_video.terminate()
            self.th_video = None
        if self._current_camera:
            self._capture = False
            frame_queue = self._camera_launcher.camera_start(self._current_camera)
            self.th_video = VideoThread(self, frame_queue)
            self.th_video.on_recv_frame.connect(self.on_receive_frame)
            self.th_video.start()

    def on_mute_changed(self):
        self.play_audio()

    def on_audio_changed(self):
        self.play_audio()

    def on_joystick_changed(self):
        if self._current_joystick:
            self._current_joystick.stop()
            self._current_joystick = None

        if self._joystick_timer:
            self._joystick_timer.stop()
            self._joystick_timer = None

        self.chkJoystickButtonSwitch.setChecked(False)
        if self.cbxJoystickList.currentIndex() == 0:
            return

        joystick_info = self._joystick_devices[self.cbxJoystickList.currentIndex(
        ) - 1]
        self._current_joystick = Joystick(self, joystick_info)
        self._current_joystick.joystick_event.connect(
            self._joystick_controller_event)
        if joystick_info.name != "Nintendo Switch Pro Controller":
            self.chkJoystickButtonSwitch.setChecked(True)
        else:
            self.chkJoystickButtonSwitch.setChecked(False)

        self._joystick_timer = QTimer()
        self._joystick_timer.timeout.connect(self._current_joystick.run)
        self._joystick_timer.start(1)

    def on_joystick_button_switch_changed(self):
        if self._current_joystick:
            self._current_joystick.setButtonSwitch(
                self.chkJoystickButtonSwitch.isChecked())

    def on_serial_changed(self):
        self._controller_launcher.controller_stop()
        if self.cbxSerialList.currentIndex() == 0:
            return
        self._controller_input_action_queue = self._controller_launcher.controller_start(self._serial_devices[self.cbxSerialList.currentIndex() - 1])
        time.sleep(0.5)
        if not self._controller_launcher.controller_running():
            self._controller_launcher.controller_stop()
            self._controller_input_action_queue = None
            self.pop_switch_pro_controller_err_dialog()

    def on_toolBox_current_changed(self, index):
        if index != 1:
            if not self.check_macro_thread_running():
                self.toolBox.setCurrentIndex(1)

    def pop_switch_pro_controller_err_dialog(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText("NS控制设备连接错误")
        msg_box.setInformativeText("请检查设备连接或选择其他设备")
        msg_box.setWindowTitle("错误")
        msg_box.exec_()
        self.cbxSerialList.setCurrentIndex(0)

    def check_macro_thread_running(self):
        if self._macro_launcher.macro_running():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText("脚本正在运行")
            msg_box.setInformativeText("是否停止正在运行脚本")
            msg_box.setWindowTitle("提示")
            msg_box.addButton('确定', QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton('取消', QMessageBox.ButtonRole.RejectRole)
            ret = msg_box.exec_()
            if ret == QMessageBox.ButtonRole.ActionRole.value:
                if not self._macro_launcher.macro_stop():
                    send_log("已强行终止运行中脚本")
                self.on_serial_changed()
                return True
            return False
        return True
    
    def on_capture_clicked(self):
        self._capture = True
        # self._camera_launcher.put_nowait("camera")

    def on_rescan_clicked(self):
        self.build_camera_list_comboBox()
        self.build_audio_list_comboBox()

    def on_serial_rescan_clicked(self):
        self.build_serial_device_list_comboBox()

    def on_joystick_rescan_clicked(self):
        self.build_joystick_device_list_comboBox()

    @Slot()
    def _readyRead(self):
        data = self._io_device.readAll()
        self._m_output.write(data)

    def closeEvent(self, event):
        self._camera_launcher.camera_stop()
        self._macro_launcher.macro_stop()
        self._controller_launcher.controller_stop()
        if self._current_joystick:
            self._current_joystick.stop()
            self._current_joystick = None
        if self._joystick_timer:
            self._joystick_timer.stop()
            self._joystick_timer = None
        if self._timer:
            self._timer.stop()
        self.stop_audio()
        if self.th_video:
            self.th_video.terminate()
        if self.th_display:
            self.th_display.terminate()
        if self.th_log:
            self.th_log.terminate()
        if self.th_action_display:
            self.th_action_display.terminate()
        pygame.quit()
        event.accept()
        QCoreApplication.instance().aboutToQuit.emit()

    @Slot()
    def on_destroy(self):
        print('on_destroy')

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
        if self._current_camera != None:
            # .scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
            pixmap = QPixmap.fromImage(img)
            self.lblCameraFrame.setPixmap(pixmap)
        else:
            self.lblCameraFrame.clear()

    def on_receive_frame(self, frame):
        if self._display_frame_queue.empty():
            self._display_frame_queue.put_nowait(frame)
        if self._capture:
            np_array = numpy.frombuffer(
                frame.bytes(), dtype=numpy.uint8)
            mat = np_array.reshape(
                (frame.height, frame.width, frame.channels))
            if not os.path.exists("./Captures"):
                os.mkdir("./Captures")
            time_str = time.strftime(
                "%Y%m%d%H%M%S", time.localtime())
            cv2.imwrite("./Captures/"+time_str+".jpg", mat)
            self._capture = False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            self._key_press_map[event.key()] = time.monotonic()
        elif event.type() == QEvent.Type.KeyRelease:
            self._key_press_map.pop(event.key(), None)
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
            self._key_press_map.pop(Qt.Key_A, None)
            self._key_press_map.pop(Qt.Key_S, None)
            self._key_press_map.pop(Qt.Key_D, None)
            self._key_press_map.pop(Qt.Key_W, None)
        if self._key_press_map.get(Qt.Key_A) and self._key_press_map.get(Qt.Key_D):
            self._key_press_map.pop(Qt.Key_A, None)
            self._key_press_map.pop(Qt.Key_D, None)
        if self._key_press_map.get(Qt.Key_S) and self._key_press_map.get(Qt.Key_W):
            self._key_press_map.pop(Qt.Key_S, None)
            self._key_press_map.pop(Qt.Key_W, None)

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
            self._key_press_map.pop(Qt.Key_Semicolon, None)
            self._key_press_map.pop(Qt.Key_Comma, None)
            self._key_press_map.pop(Qt.Key_Period, None)
            self._key_press_map.pop(Qt.Key_Slash, None)
        if self._key_press_map.get(Qt.Key_Semicolon) and self._key_press_map.get(Qt.Key_Period):
            self._key_press_map.pop(Qt.Key_Semicolon, None)
            self._key_press_map.pop(Qt.Key_Period, None)
        if self._key_press_map.get(Qt.Key_Period) and self._key_press_map.get(Qt.Key_Slash):
            self._key_press_map.pop(Qt.Key_Period, None)
            self._key_press_map.pop(Qt.Key_Slash, None)

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
            self._key_press_map.pop(Qt.Key_F, None)
            self._key_press_map.pop(Qt.Key_C, None)
            self._key_press_map.pop(Qt.Key_V, None)
            self._key_press_map.pop(Qt.Key_B, None)
        if self._key_press_map.get(Qt.Key_F) and self._key_press_map.get(Qt.Key_V):
            self._key_press_map.pop(Qt.Key_F, None)
            self._key_press_map.pop(Qt.Key_V, None)
        if self._key_press_map.get(Qt.Key_C) and self._key_press_map.get(Qt.Key_B):
            self._key_press_map.pop(Qt.Key_C, None)
            self._key_press_map.pop(Qt.Key_B, None)

        input = ControllerInput()
        if self._key_press_map.get(Qt.Key_L):
            input.set_button(InputEnum.BUTTON_A)
        if self._key_press_map.get(Qt.Key_K):
            input.set_button(InputEnum.BUTTON_B)
        if self._key_press_map.get(Qt.Key_I):
            input.set_button(InputEnum.BUTTON_X)
        if self._key_press_map.get(Qt.Key_J):
            input.set_button(InputEnum.BUTTON_Y)
        if self._key_press_map.get(Qt.Key_R):
            input.set_button(InputEnum.BUTTON_MINUS)
        if self._key_press_map.get(Qt.Key_H):
            input.set_button(InputEnum.BUTTON_HOME)
        if self._key_press_map.get(Qt.Key_Y):
            input.set_button(InputEnum.BUTTON_PLUS)
        if self._key_press_map.get(Qt.Key_X):
            input.set_button(InputEnum.BUTTON_LPRESS)
        if self._key_press_map.get(Qt.Key_Apostrophe):
            input.set_button(InputEnum.BUTTON_RPRESS)
        if self._key_press_map.get(Qt.Key_E):
            input.set_button(InputEnum.BUTTON_L)
        if self._key_press_map.get(Qt.Key_U):
            input.set_button(InputEnum.BUTTON_R)
        if self._key_press_map.get(Qt.Key_F):
            input.set_button(InputEnum.DPAD_TOP)
        if self._key_press_map.get(Qt.Key_V):
            input.set_button(InputEnum.DPAD_BOTTOM)
        if self._key_press_map.get(Qt.Key_C):
            input.set_button(InputEnum.DPAD_LEFT)
        if self._key_press_map.get(Qt.Key_B):
            input.set_button(InputEnum.DPAD_RIGHT)
        if self._key_press_map.get(Qt.Key_G):
            input.set_button(InputEnum.BUTTON_CAPTURE)
        if self._key_press_map.get(Qt.Key_Q):
            input.set_button(InputEnum.BUTTON_ZL)
        if self._key_press_map.get(Qt.Key_O):
            input.set_button(InputEnum.BUTTON_ZR)
        x = 0
        y = 0
        if self._key_press_map.get(Qt.Key_W):
            y = -127
        elif self._key_press_map.get(Qt.Key_S):
            y = 127
        if self._key_press_map.get(Qt.Key_A):
            x = -127
        elif self._key_press_map.get(Qt.Key_D):
            x = 127
        input.set_stick(StickEnum.LSTICK, x, y)

        x = 0
        y = 0
        if self._key_press_map.get(Qt.Key_Semicolon):
            y = -127
        elif self._key_press_map.get(Qt.Key_Period):
            y = 127
        if self._key_press_map.get(Qt.Key_Slash):
            x = 127
        elif self._key_press_map.get(Qt.Key_Comma):
            x = -127
        input.set_stick(StickEnum.RSTICK, x, y)

        self._current_controller_input_keyboard = input
        return QtWidgets.QMainWindow.eventFilter(self, obj, event)

    def realtime_control_action_send(self):
        if self.cbxSerialList.currentIndex() > 0 and self.toolBox.currentIndex() == 0:
            input = ControllerInput()
            if self._current_controller_input_joystick:
                input = self._current_controller_input_joystick
            elif self._current_controller_input_keyboard:
                input = self._current_controller_input_keyboard
            # if time.monotonic() - self._last_sent_ts > 0.01:
            ret = input.compare(self._last_sent_input)
            if ((not ret[0]) or ret[1] > 0 or ret[2] > 0 or time.monotonic() - self._last_sent_ts > 1):
                self._last_sent_input = input
                if self._controller_launcher and self._controller_launcher.controller_running():
                    self._controller_input_action_queue.put(input)
                self._last_sent_ts = time.monotonic()

    def _joystick_controller_event(self, input):
        self._current_controller_input_joystick = input

    def _set_joystick_labels(self, input):
        self._set_label_style(
            self.label_y, input.check_button(InputEnum.BUTTON_Y))
        self._set_label_style(
            self.label_x, input.check_button(InputEnum.BUTTON_X))
        self._set_label_style(
            self.label_b, input.check_button(InputEnum.BUTTON_B))
        self._set_label_style(
            self.label_a, input.check_button(InputEnum.BUTTON_A))
        self._set_label_style(
            self.label_l, input.check_button(InputEnum.BUTTON_L))
        self._set_label_style(
            self.label_r, input.check_button(InputEnum.BUTTON_R))
        self._set_label_style(
            self.label_zl, input.check_button(InputEnum.BUTTON_ZL))
        self._set_label_style(
            self.label_zr, input.check_button(InputEnum.BUTTON_ZR))
        self._set_label_style(
            self.label_minus, input.check_button(InputEnum.BUTTON_MINUS))
        self._set_label_style(
            self.label_plus, input.check_button(InputEnum.BUTTON_PLUS))
        self._set_label_style(self.label_lstick_press,
                              input.check_button(InputEnum.BUTTON_LPRESS))
        self._set_label_style(self.label_rstick_press,
                              input.check_button(InputEnum.BUTTON_RPRESS))
        self._set_label_style(
            self.label_home, input.check_button(InputEnum.BUTTON_HOME))
        self._set_label_style(self.label_capture,
                              input.check_button(InputEnum.BUTTON_CAPTURE))
        self._set_label_style(
            self.label_dpad_t, input.check_button(InputEnum.DPAD_TOP))
        self._set_label_style(
            self.label_dpad_r, input.check_button(InputEnum.DPAD_RIGHT))
        self._set_label_style(
            self.label_dpad_b, input.check_button(InputEnum.DPAD_BOTTOM))
        self._set_label_style(
            self.label_dpad_l, input.check_button(InputEnum.DPAD_LEFT))
        buffer = input.get_buffer()
        self._set_stick_label_style(
            self.label_lstick_l, (buffer[3] - 0x80) * (-1))
        self._set_stick_label_style(self.label_lstick_r, (buffer[3] - 0x80))
        self._set_stick_label_style(
            self.label_lstick_t, (buffer[4] - 0x80) * (-1))
        self._set_stick_label_style(self.label_lstick_b, (buffer[4] - 0x80))
        self._set_stick_label_style(
            self.label_rstick_l, (buffer[5] - 0x80) * (-1))
        self._set_stick_label_style(self.label_rstick_r, (buffer[5] - 0x80))
        self._set_stick_label_style(
            self.label_rstick_t, (buffer[6] - 0x80) * (-1))
        self._set_stick_label_style(self.label_rstick_b, (buffer[6] - 0x80))
        self.label_action.setText("实时命令：{}".format(input.get_action_line()))
        # if self._current_joystick:
        #     pygame.event.get()
        #     axes = [self._current_joystick.get_axis(i) for i in range(self._current_joystick.get_numaxes())]
        #     buttons = [self._current_joystick.get_button(i) for i in range(self._current_joystick.get_numbuttons())]
        #     hats = [self._current_joystick.get_hat(i) for i in range(self._current_joystick.get_numhats())]
        #     self.label_action.setText("实时命令：{} {}".format(axes,hats))

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

    def _set_label_style(self, label, pushed):
        if pushed:
            label.setStyleSheet(u"background-color:rgb(0, 0, 255)")
        else:
            label.setStyleSheet(u"background-color:rgb(170, 170, 170)")

    def _set_stick_label_style(self, label: QLabel, v: int):
        if v > 127:
            v = 127
        ret = round(v / 127.0 * 1000)
        if ret < 0:
            ret = 0
        color = self._stick_label_gradient_colors[ret]
        label.setStyleSheet(
            u"background-color:rgb({},{},{})".format(color[0], color[1], color[2]))

    def _gradient(self, start_color, end_color, steps):
        # 将RGB颜色转换为三个分量
        start_r, start_g, start_b = start_color
        end_r, end_g, end_b = end_color

        # 计算每个分量的步长
        r_step = (end_r - start_r) / (steps - 1)
        g_step = (end_g - start_g) / (steps - 1)
        b_step = (end_b - start_b) / (steps - 1)

        # 生成渐变颜色列表
        gradient_colors = []
        for i in range(steps):
            r = math.floor(start_r + i * r_step)
            g = math.floor(start_g + i * g_step)
            b = math.floor(start_b + i * b_step)
            gradient_colors.append((r, g, b))

        return gradient_colors

    @Slot(str)
    def setLog(self, log):
        now_str = datetime.datetime.now().strftime('%H:%M:%S')
        self.textBrowserLog.append("{}\t{}".format(now_str,log))

    @Slot(ControllerInput)
    def displayAction(self, action):
        self._set_joystick_labels(action)

        