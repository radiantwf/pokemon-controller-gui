import time
from ui.controller.device import SerialDevice
import serial

from ui.controller.input import ControllerInput

class SwitchProControll(object):
    def __init__(self):
        self._device = None

    def open(self,device_info:SerialDevice):
        self.close()
        try:
            self._device = serial.Serial(device_info.path,device_info.baudrate,timeout=1)
        except:
            return False
        return True


    def close(self):
        if self._device == None:
            return
        try:
            self._device.close()
            self._device = None
        except:
            pass

    def send_action(self,input:ControllerInput):
        if self._device == None:
            return
        try:
            self._device.write(input.get_action_buffer())
        except:
            pass
    
    def read_line(self)->str:
        if self._device == None:
            return ""
        return self._device.readline().decode("utf-8").strip()