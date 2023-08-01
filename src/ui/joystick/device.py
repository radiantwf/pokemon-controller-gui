import pygame


class JoystickDevice(object):
    def __init__(self, name: str, guid: str):
        self._name = name
        self._guid = guid

    @property
    def name(self):
        return self._name

    @property
    def guid(self):
        return self._guid

    @staticmethod
    def list_device():
        devices = []
        for i in range(pygame.joystick.get_count()):
            try:
                joystick = pygame.joystick.Joystick(i)
            except:
                continue
            devices.append(JoystickDevice(
                joystick.get_name(), joystick.get_guid()))
        return devices
