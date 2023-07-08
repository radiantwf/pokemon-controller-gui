
import random
import time
from PySide6.QtCore import QThread, Signal
import socket
import sys
import os
from const import ConstClass
from ui.controller.input import ControllerInput


class ControllerThread(QThread):
    push_action = Signal(ControllerInput)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._udp_socket = None
        self._port = 0
        self._stop_signal = False
        self._local_addr = None
        self._my_const = ConstClass()

    def refresh_service(self) -> int:
        sock = self._udp_socket
        self._udp_socket = None
        self._port = 0
        if sock:
            sock.close()
        port = random.randint(40000, 60000)
        while True:
            if self._my_const.AF_UNIX_FLAG:
                local_addr = "/tmp/poke_ui_controller_{}.sock".format(port)
                if os.path.exists(local_addr):
                    port = random.randint(40000, 60000)
                    continue
                del_addr = self._local_addr
                self._local_addr = local_addr
                if del_addr and os.path.exists(del_addr):
                    os.remove(del_addr)
                break
            else:
                self._local_addr = None
                try:
                    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    local_addr = ("127.0.0.1", port)
                    sock2.bind(local_addr)
                    sock2.close()
                    break
                except:
                    port = random.randint(40000, 60000)
                    continue
        self._port = port
        return port

    def run(self):
        while True:
            if self._stop_signal:
                break
            if self._udp_socket == None and self._port > 0:
                try:
                    if self._my_const.AF_UNIX_FLAG:
                        if not os.path.exists(self._local_addr):
                            self._udp_socket = socket.socket(
                                socket.AF_UNIX, socket.SOCK_DGRAM)
                            self._udp_socket.bind(self._local_addr)
                            self._udp_socket.setblocking(False)
                    else:
                        self._udp_socket = socket.socket(
                            socket.AF_INET, socket.SOCK_DGRAM)
                        local_addr = ("127.0.0.1", self._port)
                        self._udp_socket.bind(local_addr)
                        self._udp_socket.setblocking(False)
                except:
                    self._udp_socket.close()
                    self._udp_socket = None
            if not self._udp_socket:
                time.sleep(0.1)
                continue
            recv_data = None
            while True:
                try:
                    if self._stop_signal:
                        break
                    recv_data = self._udp_socket.recvfrom(1024)
                except:
                    break
            if recv_data != None:
                recv_msg = recv_data[0].decode("utf-8").strip()
                self.push_action.emit(ControllerInput(recv_msg))
            else:
                time.sleep(0.001)

    def stop(self):
        self._stop_signal = True

    def __del__(self):
        try:
            self.stop()
            self.wait()
        except:
            pass
