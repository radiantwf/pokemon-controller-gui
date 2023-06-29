
import random
import time
from PySide6.QtCore import QThread,Signal
import socket

class ControllerThread(QThread):
    push_action = Signal(str)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._udp_socket = None
        self._port = 0
        self._stop_signal = False

    def refresh_service(self)->int:
        sock = self._udp_socket
        self._udp_socket = None
        self._port = 0
        if sock:
            sock.close()
        port = random.randint(40000,60000)
        while True:
            try:
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
                local_addr = ("127.0.0.1", port)
                sock2.bind(local_addr)
                sock2.close()
                break
            except:
                port = random.randint(40000,60000)
                continue
        self._port = port
        return port

    def run(self):
        while True:
            if self._stop_signal:
                break
            if self._udp_socket == None and self._port > 0:
                try:
                    self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
                    local_addr = ("127.0.0.1", self._port)
                    self._udp_socket.bind(local_addr)
                    self._udp_socket.setblocking(True)
                    self._udp_socket.settimeout(0.001)
                except Exception as e:
                    self._udp_socket.close()
                    self._udp_socket = None
                    time.sleep(0.001)
            recv_data = None
            try:
                recv_data = self._udp_socket.recvfrom(1024)
            except Exception as e:
                pass
            if recv_data != None:
                recv_msg = recv_data[0].decode("utf-8").strip()
                self.push_action.emit(recv_msg)

    def stop(self):
        self._stop_signal = True

    def __del__(self):
        self.stop()
        self.wait()
