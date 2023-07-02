import time
import pygame
from ui.controller.input import ControllerInput, InputEnum, StickEnum
from PySide6.QtCore import Signal

from ui.joystick.device import JoystickDevice

class Joystick(object):
    def __init__(self, joystick_info,joystick_event):
        self._stop_signal = False
        self._joystick = self._open_joystick(joystick_info)
        self._chkJoystickButtonSwitch = False
        self._joystick_event = joystick_event
        if self._joystick == None:
            return

    def setButtonSwitch(self,chkJoystickButtonSwitch:bool):
        self._chkJoystickButtonSwitch = chkJoystickButtonSwitch
    
    def loop_event(self):
        if self._joystick == None:
            return
        self._joystick.init()
        while True:
            if self._stop_signal:
                break
            pygame.event.get()
            axes = [self._joystick.get_axis(i) for i in range(self._joystick.get_numaxes())]
            buttons = [self._joystick.get_button(i) for i in range(self._joystick.get_numbuttons())]
            hats = [self._joystick.get_hat(i) for i in range(self._joystick.get_numhats())]
            input = ControllerInput()
            if self._chkJoystickButtonSwitch:
                if buttons[0]:
                    input.set_button(InputEnum.BUTTON_A)
                if buttons[1]:
                    input.set_button(InputEnum.BUTTON_B)
                if buttons[2]:
                    input.set_button(InputEnum.BUTTON_Y)
                if buttons[3]:
                    input.set_button(InputEnum.BUTTON_X)
            else:
                if buttons[0]:
                    input.set_button(InputEnum.BUTTON_B)
                if buttons[1]:
                    input.set_button(InputEnum.BUTTON_A)
                if buttons[2]:
                    input.set_button(InputEnum.BUTTON_X)
                if buttons[3]:
                    input.set_button(InputEnum.BUTTON_Y)
            if buttons[4]:
                input.set_button(InputEnum.BUTTON_MINUS)
            if buttons[5]:
                input.set_button(InputEnum.BUTTON_HOME)
            if buttons[6]:
                input.set_button(InputEnum.BUTTON_PLUS)
            if buttons[7]:
                input.set_button(InputEnum.BUTTON_LPRESS)
            if buttons[8]:
                input.set_button(InputEnum.BUTTON_RPRESS)
            if buttons[9]:
                input.set_button(InputEnum.BUTTON_L)
            if buttons[10]:
                input.set_button(InputEnum.BUTTON_R)
            if buttons[11]:
                input.set_button(InputEnum.DPAD_TOP)
            if buttons[12]:
                input.set_button(InputEnum.DPAD_LEFT)
            if buttons[13]:
                input.set_button(InputEnum.DPAD_BOTTOM)
            if buttons[14]:
                input.set_button(InputEnum.DPAD_RIGHT)
            if buttons[15]:
                input.set_button(InputEnum.BUTTON_CAPTURE)
            if axes[4]>=0.5:
                input.set_button(InputEnum.BUTTON_ZL)
            if axes[5]>=0.5:
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
            x = round((axes[0]+1)/2*0xFF) - 0x80
            y = round((axes[1]+1)/2*0xFF) - 0x80
            input.set_stick(StickEnum.LSTICK,x,y)
            x = round((axes[2]+1)/2*0xFF) - 0x80
            y = round((axes[3]+1)/2*0xFF) - 0x80
            input.set_stick(StickEnum.RSTICK,x,y)
            if self._joystick_event:
                self._joystick_event(input)

        if self._joystick_event:
            self._joystick_event(ControllerInput())
        self._joystick.quit()

    def stop(self):
        self._stop_signal = True
        time.sleep(0.1)

    def _open_joystick(self,dev:JoystickDevice):
        joystick = None
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            if joystick.get_guid() == dev.guid:
                break
            joystick = None
        return joystick