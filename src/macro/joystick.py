
import socket
from const import ConstClass


class JoyStick(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(JoyStick, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self, port: int = 50000):
        if JoyStick._first:
            JoyStick._first = False
            self._my_const = ConstClass()
            self._port = port

    def send_action(self, action: str = ""):
        if action == "":
            action = " "
        if self._port > 0 and self._port < 65535:
            if self._my_const.AF_UNIX_FLAG:
                client = socket.socket(
                    socket.AF_UNIX, socket.SOCK_DGRAM)
                local_addr = "/tmp/poke_ui_controller_{}.sock".format(
                    self._port)
                client.sendto(action.encode(
                    "utf-8"), local_addr)
                client.close()
            else:
                client = socket.socket(
                    socket.AF_INET, socket.SOCK_DGRAM)
                client.sendto(action.encode(
                    "utf-8"), ("127.0.0.1", self._port))
                client.close()
