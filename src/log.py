import socket
from const import ConstClass

def send_log(log:str):
    _my_const = ConstClass()
    if _my_const.AF_UNIX_FLAG:
        client = socket.socket(
            socket.AF_UNIX, socket.SOCK_DGRAM)
        local_addr = "/tmp/poke_ui_log_{}.sock".format(
            _my_const.LogSocketPort)
        client.sendto(log.encode(
            "utf-8"), local_addr)
        client.close()
    else:
        client = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        client.sendto(log.encode(
            "utf-8"), ("127.0.0.1", _my_const.LogSocketPort))
        client.close()