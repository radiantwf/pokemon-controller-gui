
import os
import socket
import time
from PySide6.QtCore import QThread, Signal

from const import ConstClass
from datatype.input import ControllerInput


class ActionDisplayThread(QThread):
    action = Signal(ControllerInput)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._stop_signal = False
        self._my_const = ConstClass()
        self._udp_socket = None

    def run(self):
        while True:
            if self._stop_signal:
                break
            try:
                if self._udp_socket:
                    s = self._udp_socket
                    self._udp_socket = None
                    s.close()

                if self._my_const.AF_UNIX_FLAG:
                    local_addr = "/tmp/poke_ui_action_{}.sock".format(
                        self._my_const.ActionDisplaySocketPort)
                    if os.path.exists(local_addr):
                        os.remove(local_addr)
                    self._udp_socket = socket.socket(
                        socket.AF_UNIX, socket.SOCK_DGRAM)
                    self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
                    self._udp_socket.bind(local_addr)
                else:
                    self._udp_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM)
                    local_addr = ("127.0.0.1", self._my_const.ActionDisplaySocketPort)
                    self._udp_socket.bind(local_addr)
                self._udp_socket.setblocking(False)
                while True:
                    if self._stop_signal:
                        break
                    recv_data = None
                    try:
                        recv_data = self._udp_socket.recvfrom(1024)
                    except Exception as e:
                        pass
                    if recv_data != None:
                        recv_msg = recv_data[0].decode("utf-8").strip()
                        self.action.emit(ControllerInput(recv_msg))
                    time.sleep(0.001)
            except:
                continue

    def stop(self):
        self._stop_signal = True
        if self._udp_socket:
            self._udp_socket.close()

    def __del__(self):
        try:
            self.stop()
            self.wait()
        except:
            pass
