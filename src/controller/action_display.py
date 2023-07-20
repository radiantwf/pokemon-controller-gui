import socket
from const import ConstClass
from datatype.input import ControllerInput

def send_action_display(action:ControllerInput):
    _my_const = ConstClass()
    if _my_const.AF_UNIX_FLAG:
        client = socket.socket(
            socket.AF_UNIX, socket.SOCK_DGRAM)
        local_addr = "/tmp/poke_ui_action_{}.sock".format(
            _my_const.ActionDisplaySocketPort)
        client.sendto(action.get_action_line().encode(
            "utf-8"), local_addr)
        client.close()
    else:
        client = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        client.sendto(action.get_action_line().encode(
            "utf-8"), ("127.0.0.1", _my_const.ActionDisplaySocketPort))
        client.close()