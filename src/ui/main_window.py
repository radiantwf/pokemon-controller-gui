import datetime
import math
import multiprocessing
import os
import platform
import queue
import time
import cv2
import numpy
import pygame
from const import ConstClass
from PySide6 import QtWidgets
from PySide6.QtWidgets import QMessageBox, QLabel, QListWidgetItem, QTreeWidgetItem
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
from ui.recognition.dialog import LaunchRecognitionParasDialog

from ui.recognition.launcher import RecognitionLauncher
from recognition.scripts.parameter_struct import ScriptParameter
Ui_MainWindow, QMainWindowBase = loadUiType("./resources/ui/main_form.ui")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        # 控制器输入命令队列
        self._controller_input_action_queue: multiprocessing.Queue = None

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
        self._last_operation_type = None

        start_color = (170, 170, 170)
        end_color = (0, 0, 255)
        steps = 1001
        self._stick_label_gradient_colors = self._gradient(
            start_color, end_color, steps)

        self._display_frame_queue = multiprocessing.Queue(1)
        self._recognition_frame_queue = multiprocessing.Queue(1)

        self._macro_list = []
        self._macro_launcher = MacroLauncher()
        self._last_macro_scripts = dict()
        self._macro_script_group_delimiter = "-"
        self._macro_tree = None
        self._recognition_list = []
        self._recognition_launcher = RecognitionLauncher()
        self._last_recognition_scripts = dict()
        self._recognition_script_group_delimiter = "-"
        self._recognition_tree = None
        self._script_tree_indent = 8
        self._controller_launcher = ControllerLauncher()
        self._camera_launcher = CameraLauncher()

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        if platform.system() == 'Darwin':
            self.btn_macro_redo.setText("重做(Cmd+R)")
            self.btn_recognition_redo.setText("重做(Cmd+R)")

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
        self.btnClearLog.clicked.connect(self.clear_log)

        self.th_log = LogThread(self)
        self.th_log.log.connect(self.setLog)
        self.th_log.start()

        self.th_display = DisplayThread(self, self._display_frame_queue)
        self.th_display.display_frame.connect(self.display_frame)
        self.th_display.start()

        self.th_action_display = ActionDisplayThread(self)
        self.th_action_display.action.connect(self.displayAction)
        self.th_action_display.start()

        self.chkJoystickButtonSwitch.stateChanged.connect(
            self.on_joystick_button_switch_changed)

        self.chkJoystickTriggerModel2.stateChanged.connect(
            self.on_joystick_trigger_dualsense_changed)

        self.toolBox.setCurrentIndex(0)

        self._timer = QTimer()
        self._timer.timeout.connect(self.realtime_control_action_send)
        self._timer.start(1)

        self.build_macro_list_listView()
        self._setup_recognition_tree()
        self.build_recognition_list_listView()

        self.btn_macro_opt.clicked.connect(self.macro_opt)
        self.btn_macro_redo.clicked.connect(self.macro_redo)
        self.btn_recognition_opt.clicked.connect(self.recognition_opt)
        self.btn_recognition_redo.clicked.connect(self.recognition_redo)

        self.btn_macro_refresh.clicked.connect(self.macro_refresh)

    def _trigger_page_redo(self):
        page = self.toolBox.currentWidget()
        if page is None:
            return
        page_name = page.objectName()
        if page_name == "page_macro":
            self.btn_macro_redo.click()
        elif page_name == "page_recognition":
            self.btn_recognition_redo.click()
        elif page_name == "page_realtime":
            if self._last_operation_type == "macro":
                self.toolBox.setCurrentIndex(1)
                self.btn_macro_redo.click()
            elif self._last_operation_type == "recognition":
                self.toolBox.setCurrentIndex(2)
                self.btn_recognition_redo.click()

    def _setup_macro_tree(self):
        if getattr(self, "treeWidget_macro", None) is not None:
            self._macro_tree = self.treeWidget_macro
            return
        geo = self.listWidget_macro.geometry()
        parent = self.listWidget_macro.parent()
        self.treeWidget_macro = QtWidgets.QTreeWidget(parent)
        self.treeWidget_macro.setGeometry(geo)
        self.treeWidget_macro.setHeaderHidden(True)
        self.treeWidget_macro.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.treeWidget_macro.setIndentation(self._script_tree_indent)
        self.listWidget_macro.hide()
        self._macro_tree = self.treeWidget_macro

    def _setup_recognition_tree(self):
        if getattr(self, "treeWidget_recognition", None) is not None:
            self._recognition_tree = self.treeWidget_recognition
            return
        geo = self.listWidget_recognition.geometry()
        parent = self.listWidget_recognition.parent()
        self.treeWidget_recognition = QtWidgets.QTreeWidget(parent)
        self.treeWidget_recognition.setGeometry(geo)
        self.treeWidget_recognition.setHeaderHidden(True)
        self.treeWidget_recognition.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.treeWidget_recognition.setIndentation(self._script_tree_indent)
        self.listWidget_recognition.hide()
        self._recognition_tree = self.treeWidget_recognition

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
        if self._macro_tree is None:
            self._setup_macro_tree()
        self._macro_tree.clear()

        root_items: dict[str, QTreeWidgetItem] = dict()
        delimiter = self._macro_script_group_delimiter
        for macro in self._macro_list:
            summary = macro.get("summary")
            if not summary:
                continue
            parts = [p.strip() for p in str(summary).split(delimiter) if p.strip() != ""]
            if not parts:
                continue
            current_item = None
            for idx, part in enumerate(parts):
                is_leaf = idx == len(parts) - 1
                if current_item is None:
                    if part not in root_items:
                        root_items[part] = QTreeWidgetItem([part])
                        root_items[part].setData(0, Qt.UserRole, None)
                        self._macro_tree.addTopLevelItem(root_items[part])
                    current_item = root_items[part]
                else:
                    child = None
                    for i in range(current_item.childCount()):
                        if current_item.child(i).text(0) == part:
                            child = current_item.child(i)
                            break
                    if child is None:
                        child = QTreeWidgetItem([part])
                        child.setData(0, Qt.UserRole, None)
                        current_item.addChild(child)
                    current_item = child

                if is_leaf:
                    current_item.setToolTip(0, str(macro.get("summary", "")))
                    current_item.setData(0, Qt.UserRole, macro)

        def compress(item: QTreeWidgetItem):
            changed = True
            while changed:
                changed = False
                if item.childCount() == 1:
                    child = item.child(0)
                    if child is not None and child.childCount() > 0:
                        item.setText(0, f"{item.text(0)}{delimiter}{child.text(0)}")
                        item.takeChild(0)
                        while child.childCount() > 0:
                            item.addChild(child.takeChild(0))
                        changed = True
            for i in range(item.childCount()):
                compress(item.child(i))

        for i in range(self._macro_tree.topLevelItemCount()):
            compress(self._macro_tree.topLevelItem(i))

        def mark_selectable(item: QTreeWidgetItem):
            is_leaf = item.childCount() == 0 and item.data(0, Qt.UserRole) is not None
            if not is_leaf:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            for i in range(item.childCount()):
                mark_selectable(item.child(i))

        for i in range(self._macro_tree.topLevelItemCount()):
            mark_selectable(self._macro_tree.topLevelItem(i))

        def sort_item(item: QTreeWidgetItem):
            item.sortChildren(0, Qt.SortOrder.AscendingOrder)
            for i in range(item.childCount()):
                sort_item(item.child(i))

        self._macro_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        for i in range(self._macro_tree.topLevelItemCount()):
            sort_item(self._macro_tree.topLevelItem(i))

        self._macro_tree.collapseAll()

    def macro_opt(self):
        macro = self._current_macro_script()
        if macro is None:
            return
        if not self.check_macro_thread_running():
            return

        self.on_serial_changed()

        if not self._controller_input_action_queue:
            return
        dialog = LaunchMacroParasDialog(self, macro)
        ret = dialog.exec_()
        if ret == QtWidgets.QDialog.Accepted:
            script = dialog.get_macro_script()
            paras = dict()
            for para in script["paras"]:
                paras[para["name"]] = para["value"]
            self._last_macro_scripts[script["name"]] = dict(
                {"loop": script["loop"], "paras": paras.copy()})
            self._macro_launcher.macro_start(
                script["name"], self._controller_input_action_queue, script["loop"], paras)
            self._last_operation_type = "macro"

    def macro_redo(self):
        macro = self._current_macro_script()
        if macro is None:
            return
        if not self.check_macro_thread_running():
            return

        self.on_serial_changed()

        if not self._controller_input_action_queue:
            return
        if "name" not in macro:
            return
        script_name = macro["name"]
        if script_name not in self._last_macro_scripts:
            return
        last = self._last_macro_scripts[script_name]
        loop = last.get("loop", 1)
        paras = last.get("paras", dict()).copy()
        self._macro_launcher.macro_start(
            script_name, self._controller_input_action_queue, loop, paras)
        self._last_operation_type = "macro"

    def macro_refresh(self):
        self.build_macro_list_listView()

    def _current_macro_script(self):
        if self._macro_tree is None:
            return None
        item = self._macro_tree.currentItem()
        if item is None:
            return None
        if item.childCount() != 0:
            return None
        value = item.data(0, Qt.UserRole)
        if not isinstance(value, dict):
            return None
        return value

    def build_recognition_list_listView(self):
        self._recognition_list = self._recognition_launcher.list_recognition()
        if self._recognition_tree is None:
            self._setup_recognition_tree()
        self._recognition_tree.clear()

        root_items: dict[str, QTreeWidgetItem] = dict()
        delimiter = self._recognition_script_group_delimiter
        for recognition in self._recognition_list:
            parts = [p.strip() for p in str(recognition).split(delimiter) if p.strip() != ""]
            if not parts:
                continue
            current_item = None
            for idx, part in enumerate(parts):
                is_leaf = idx == len(parts) - 1
                if current_item is None:
                    if part not in root_items:
                        root_items[part] = QTreeWidgetItem([part])
                        root_items[part].setData(0, Qt.UserRole, None)
                        self._recognition_tree.addTopLevelItem(root_items[part])
                    current_item = root_items[part]
                else:
                    child = None
                    for i in range(current_item.childCount()):
                        if current_item.child(i).text(0) == part:
                            child = current_item.child(i)
                            break
                    if child is None:
                        child = QTreeWidgetItem([part])
                        child.setData(0, Qt.UserRole, None)
                        current_item.addChild(child)
                    current_item = child

                if is_leaf:
                    current_item.setData(0, Qt.UserRole, recognition)

        def compress(item: QTreeWidgetItem):
            changed = True
            while changed:
                changed = False
                if item.childCount() == 1:
                    child = item.child(0)
                    if child is not None and child.childCount() > 0:
                        item.setText(0, f"{item.text(0)}{delimiter}{child.text(0)}")
                        item.takeChild(0)
                        while child.childCount() > 0:
                            item.addChild(child.takeChild(0))
                        changed = True
            for i in range(item.childCount()):
                compress(item.child(i))

        for i in range(self._recognition_tree.topLevelItemCount()):
            top = self._recognition_tree.topLevelItem(i)
            compress(top)

        def mark_selectable(item: QTreeWidgetItem):
            is_leaf = item.childCount() == 0 and item.data(0, Qt.UserRole) is not None
            if not is_leaf:
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            for i in range(item.childCount()):
                mark_selectable(item.child(i))

        for i in range(self._recognition_tree.topLevelItemCount()):
            mark_selectable(self._recognition_tree.topLevelItem(i))

        def sort_item(item: QTreeWidgetItem):
            item.sortChildren(0, Qt.SortOrder.AscendingOrder)
            for i in range(item.childCount()):
                sort_item(item.child(i))

        self._recognition_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        for i in range(self._recognition_tree.topLevelItemCount()):
            sort_item(self._recognition_tree.topLevelItem(i))

        self._recognition_tree.collapseAll()

    def _current_recognition_script_name(self):
        if self._recognition_tree is None:
            return None
        item = self._recognition_tree.currentItem()
        if item is None:
            return None
        if item.childCount() != 0:
            return None
        value = item.data(0, Qt.UserRole)
        if value is None:
            return None
        return value

    def recognition_opt(self):
        recognition = self._current_recognition_script_name()
        if recognition is None:
            return
        if not self.check_recognition_thread_running():
            return

        self.on_serial_changed()

        if not self._controller_input_action_queue:
            return
        paras = self._recognition_launcher.get_default_parameters(recognition)
        dialog = LaunchRecognitionParasDialog(self, paras)
        ret = dialog.exec_()
        if ret == QtWidgets.QDialog.Accepted:
            paras = dialog.get_paras()
            self._last_recognition_scripts[recognition] = self._clone_recognition_paras(
                paras)
            self._recognition_launcher.recognition_start(
                recognition, self._recognition_frame_queue, self._controller_input_action_queue, paras)
            self._last_operation_type = "recognition"

    def recognition_redo(self):
        recognition = self._current_recognition_script_name()
        if recognition is None:
            return
        if not self.check_recognition_thread_running():
            return

        self.on_serial_changed()

        if not self._controller_input_action_queue:
            return
        if recognition not in self._last_recognition_scripts:
            return
        paras = self._clone_recognition_paras(
            self._last_recognition_scripts[recognition])
        self._recognition_launcher.recognition_start(
            recognition, self._recognition_frame_queue, self._controller_input_action_queue, paras)
        self._last_operation_type = "recognition"

    def _clone_recognition_paras(self, paras: dict):
        if paras is None:
            return None
        cloned = dict()
        for name, p in paras.items():
            if not isinstance(p, ScriptParameter):
                continue
            para = ScriptParameter(p.name, p.value_type, p.default_value,
                                   p.description, p.items)
            para.set_value(p.value)
            cloned[name] = para
        return cloned

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
        if self._current_camera:
            self._capture = False
            self._camera_launcher.camera_start(
                self._current_camera, self._display_frame_queue, self._recognition_frame_queue)

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
        self.chkJoystickTriggerModel2.setChecked(False)
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

    def on_joystick_trigger_dualsense_changed(self):
        if self._current_joystick:
            self._current_joystick.setTriggerModel2(
                self.chkJoystickTriggerModel2.isChecked())

    def on_serial_changed(self):
        self._macro_launcher.macro_stop()
        self._recognition_launcher.recognition_stop()
        self._controller_launcher.controller_stop()
        if self.cbxSerialList.currentIndex() == 0:
            return
        self._controller_input_action_queue = self._controller_launcher.controller_start(
            self._serial_devices[self.cbxSerialList.currentIndex() - 1])
        time.sleep(0.5)
        if not self._controller_launcher.controller_running():
            self._controller_launcher.controller_stop()
            self._controller_input_action_queue = None
            self.pop_switch_pro_controller_err_dialog()

    def on_toolBox_current_changed(self, index):
        if index != 1:
            if not self.check_macro_thread_running():
                self.toolBox.setCurrentIndex(1)
        if index != 2:
            if not self.check_recognition_thread_running():
                self.toolBox.setCurrentIndex(2)

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
            ok_button = msg_box.addButton('确定', QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton('取消', QMessageBox.ButtonRole.RejectRole)
            msg_box.exec_()
            if msg_box.clickedButton() == ok_button:
                if not self._macro_launcher.macro_stop():
                    send_log("已强行终止运行中脚本")
                self.on_serial_changed()
                return True
            return False
        return True

    def check_recognition_thread_running(self):
        if self._recognition_launcher.recognition_running():
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText("图像识别脚本正在运行")
            msg_box.setInformativeText("是否停止正在运行脚本")
            msg_box.setWindowTitle("提示")
            ok_button = msg_box.addButton('确定', QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton('取消', QMessageBox.ButtonRole.RejectRole)
            msg_box.exec_()
            if msg_box.clickedButton() == ok_button:
                if not self._recognition_launcher.recognition_stop():
                    send_log("已强行终止运行中图像识别脚本")
                self.on_serial_changed()
                return True
            return False
        return True

    def on_capture_clicked(self):
        self._capture = True

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
        # 停止所有设备和进程
        print('camera_stop')
        self._camera_launcher.camera_stop()

        print('macro_stop')
        self._macro_launcher.macro_stop()

        print('recognition_stop')
        self._recognition_launcher.recognition_stop()

        print('controller_stop')
        self._controller_launcher.controller_stop()

        # 清理手柄相关资源
        if self._current_joystick:
            print('joystick_stop')
            self._current_joystick.stop()
            self._current_joystick = None

        # 先停止所有定时器
        if self._timer:
            print('timer_stop')
            self._timer.stop()

        if self._joystick_timer:
            print('joystick_timer_stop')
            self._joystick_timer.stop()
            self._joystick_timer = None

        # 停止音频
        print('audio_stop')
        self.stop_audio()
        # 停止所有线程
        if self.th_display:
            print('th_display_stop')
            self.th_display.terminate()
            for _ in range(10):
                if not self.th_display.isRunning():
                    break
                time.sleep(0.1)

        if self.th_log:
            print('th_log_stop')
            self.th_log.terminate()
            for _ in range(10):
                if not self.th_log.isRunning():
                    break
                time.sleep(0.1)

        if self.th_action_display:
            print('th_action_display_stop')
            self.th_action_display.terminate()
            for _ in range(10):
                if not self.th_action_display.isRunning():
                    break
                time.sleep(0.1)

        # 清理 pygame
        print('pygame_quit')
        pygame.quit()

        # 清理队列
        print('display_frame_queue_clear')
        if self._display_frame_queue:
            while not self._display_frame_queue.empty():
                try:
                    self._display_frame_queue.get_nowait()
                except queue.Empty:
                    break

        print('recognition_frame_queue_clear')
        if self._recognition_frame_queue:
            while not self._recognition_frame_queue.empty():
                try:
                    self._recognition_frame_queue.get_nowait()
                except queue.Empty:
                    break

        print('controller_input_action_queue_clear')
        if self._controller_input_action_queue:
            while not self._controller_input_action_queue.empty():
                try:
                    self._controller_input_action_queue.get_nowait()
                except queue.Empty:
                    break

        # 接受关闭事件
        print('event_accept')
        event.accept()

        # 发送退出信号
        print('aboutToQuit_emit')
        QCoreApplication.instance().aboutToQuit.emit()

    @Slot()
    def on_destroy(self):
        print('on_destroy')

    @Slot(Frame)
    def display_frame(self, frame):
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

            recognize_mat = cv2.resize(
                mat, (self._my_const.RecognizeVideoWidth, self._my_const.RecognizeVideoHeight), interpolation=cv2.INTER_AREA)
            cv2.imwrite("./Captures/{}-recognize.jpg".format(time_str),
                        recognize_mat)
            self._capture = False

        np_array = numpy.frombuffer(
            frame.bytes(), dtype=numpy.uint8)
        mat = np_array.reshape(
            (frame.height, frame.width, frame.channels))
        display_mat = cv2.resize(
            mat, (self._my_const.DisplayCameraWidth, self._my_const.DisplayCameraHeight), interpolation=cv2.INTER_AREA)
        display_frame = Frame(display_mat)

        if display_frame.format == cv2.CAP_PVAPI_PIXELFORMAT_MONO8:
            format = QImage.Format_Grayscale8
        elif display_frame.format == cv2.CAP_PVAPI_PIXELFORMAT_BGR24:
            format = QImage.Format_BGR888
        else:
            raise ValueError("Unsupported format")

        img = QImage(display_frame.bytes(), display_frame.width, display_frame.height,
                     display_frame.channels*display_frame.width, format)
        if self._current_camera != None:
            # .scaled(self.lblCameraFrame.size(), aspectMode=Qt.KeepAspectRatio)
            pixmap = QPixmap.fromImage(img)
            self.lblCameraFrame.setPixmap(pixmap)
        else:
            self.lblCameraFrame.clear()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_R and (event.modifiers() & Qt.ControlModifier):
                self._trigger_page_redo()
                return True
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
        self.textBrowserLog.append("{}\t{}".format(now_str, log))

    def clear_log(self):
        self.textBrowserLog.clear()

    @Slot(ControllerInput)
    def displayAction(self, action):
        self._set_joystick_labels(action)
