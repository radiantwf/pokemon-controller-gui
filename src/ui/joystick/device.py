import pygame

class JoystickDevice(object):
    def __init__(self,name:str,guid:str):
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
        pygame.joystick.quit()
        pygame.joystick.init()
        devices = []
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            devices.append(JoystickDevice(joystick.get_name(),joystick.get_guid()))
            joystick.quit()
        return devices

def open_joystick(dev:JoystickDevice):
    joystick = None
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        if joystick.get_guid() == dev.guid:
            break
        joystick.quit()
        joystick = None
    return joystick