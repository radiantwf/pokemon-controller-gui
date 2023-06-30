import serial.tools.list_ports


class SerialDevice(object):
    def __init__(self,name:str,path:str,baudrate:int):
        self._name = name
        self._path = path
        self._baudrate = baudrate
    
    @property
    def name(self):
        return self._name
    @property
    def path(self):
        return self._path
    @property
    def baudrate(self):
        return self._baudrate

    @staticmethod
    def list_device():
        devices = []
        ports = serial.tools.list_ports.comports()

        # 打印所有串口设备的信息
        for port in ports:
            if port.description != "n/a":
                devices.append(SerialDevice(port.name,port.device,9600))
        return devices
