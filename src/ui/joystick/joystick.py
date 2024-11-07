import pygame
from datatype.input import ControllerInput, InputEnum, StickEnum
from PySide6.QtCore import QObject, Signal

from ui.joystick.device import JoystickDevice


class Joystick(QObject):
    joystick_event = Signal(ControllerInput)

    def __init__(self, parent=None, joystick_info=None):
        QObject.__init__(self, parent)
        self._joystick = self._open_joystick(joystick_info)
        self._chkJoystickButtonSwitch = False
        self._trigger_dualsense = False
        if self._joystick == None:
            return
        self._joystick.init()
        # 只允许手柄事件进入事件队列
        pygame.event.set_allowed(
            [pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION])

    def setButtonSwitch(self, chkJoystickButtonSwitch: bool):
        self._chkJoystickButtonSwitch = chkJoystickButtonSwitch

    def setTriggerDualSense(self, trigger_dualsense: bool):
        self._trigger_dualsense = trigger_dualsense

    def run(self):
        pygame.event.pump()
        if self._joystick == None:
            return
        axes = [self._joystick.get_axis(i) for i in range(
            self._joystick.get_numaxes())]
        button_num = self._joystick.get_numbuttons()
        buttons = [self._joystick.get_button(
            i) for i in range(button_num)]
        hats = [self._joystick.get_hat(i)
                for i in range(self._joystick.get_numhats())]
        input = ControllerInput()
        if self._chkJoystickButtonSwitch:
            if buttons[0]:
                input.set_button(InputEnum.BUTTON_B)
            if buttons[1]:
                input.set_button(InputEnum.BUTTON_A)
            if buttons[2]:
                input.set_button(InputEnum.BUTTON_Y)
            if buttons[3]:
                input.set_button(InputEnum.BUTTON_X)
        else:
            if buttons[0]:
                input.set_button(InputEnum.BUTTON_A)
            if buttons[1]:
                input.set_button(InputEnum.BUTTON_B)
            if buttons[2]:
                input.set_button(InputEnum.BUTTON_X)
            if buttons[3]:
                input.set_button(InputEnum.BUTTON_Y)
        if 4 < button_num and buttons[4]:
            input.set_button(InputEnum.BUTTON_MINUS)
        if 5 < button_num and buttons[5]:
            input.set_button(InputEnum.BUTTON_HOME)
        if 6 < button_num and buttons[6]:
            input.set_button(InputEnum.BUTTON_PLUS)
        if 7 < button_num and buttons[7]:
            input.set_button(InputEnum.BUTTON_LPRESS)
        if 8 < button_num and buttons[8]:
            input.set_button(InputEnum.BUTTON_RPRESS)
        if 9 < button_num and buttons[9]:
            input.set_button(InputEnum.BUTTON_L)
        if 10 < button_num and buttons[10]:
            input.set_button(InputEnum.BUTTON_R)
        if 11 < button_num and buttons[11]:
            input.set_button(InputEnum.DPAD_TOP)
        if 12 < button_num and buttons[12]:
            input.set_button(InputEnum.DPAD_BOTTOM)
        if 13 < button_num and buttons[13]:
            input.set_button(InputEnum.DPAD_LEFT)
        if 14 < button_num and buttons[14]:
            input.set_button(InputEnum.DPAD_RIGHT)
        if 15 < button_num and buttons[15]:
            input.set_button(InputEnum.BUTTON_CAPTURE)
        if self._trigger_dualsense:
            if axes[4] >= 0.5:
                input.set_button(InputEnum.BUTTON_ZL)
            if axes[5] >= 0.5:
                input.set_button(InputEnum.BUTTON_ZR)
        else:
            if axes[2] >= 0.5:
                input.set_button(InputEnum.BUTTON_ZL)
            if axes[5] >= 0.5:
                input.set_button(InputEnum.BUTTON_ZR) 
        if hats != None and len(hats) > 1:
            if hats[0][0] == -1:
                input.set_button(InputEnum.DPAD_LEFT)
            if hats[0][0] == 1:
                input.set_button(InputEnum.DPAD_RIGHT)
            if hats[0][1] == -1:
                input.set_button(InputEnum.DPAD_TOP)
            if hats[0][1] == 1:
                input.set_button(InputEnum.DPAD_BOTTOM)

        if self._trigger_dualsense:
            x = round((axes[0]+1)/2*0xFF) - 0x80
            y = round((axes[1]+1)/2*0xFF) - 0x80
            input.set_stick(StickEnum.LSTICK, x, y)
            x = round((axes[2]+1)/2*0xFF) - 0x80
            y = round((axes[3]+1)/2*0xFF) - 0x80
            input.set_stick(StickEnum.RSTICK, x, y)
        else:
            x = round((axes[0]+1)/2*0xFF) - 0x80
            y = round((axes[1]+1)/2*0xFF) - 0x80
            input.set_stick(StickEnum.LSTICK, x, y)
            x = round((axes[3]+1)/2*0xFF) - 0x80
            y = round((axes[4]+1)/2*0xFF) - 0x80
            input.set_stick(StickEnum.RSTICK, x, y)
        if self.joystick_event:
            self.joystick_event.emit(input)

    def stop(self):
        if self._joystick != None:
            joystick = self._joystick
            self._joystick = None
            joystick.quit()
        if self.joystick_event:
            self.joystick_event.emit(None)

    def _open_joystick(self, dev: JoystickDevice):
        joystick = None
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            if joystick.get_guid() == dev.guid:
                break
            joystick = None
        return joystick
