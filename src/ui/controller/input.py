from enum import IntEnum
from io import StringIO
from math import sqrt

class InputEnum(IntEnum):
    BUTTON_Y = 0x1
    BUTTON_B = 0x2
    BUTTON_X = 0x4
    BUTTON_A = 0x8
    BUTTON_L = 0x10
    BUTTON_R = 0x20
    BUTTON_ZL = 0x40
    BUTTON_ZR = 0x80
    BUTTON_MINUS = 0x100
    BUTTON_PLUS = 0x200
    BUTTON_LPRESS = 0x400
    BUTTON_RPRESS = 0x800
    BUTTON_HOME = 0x1000
    BUTTON_CAPTURE = 0x2000
    DPAD_TOP = 0x010000
    DPAD_RIGHT = 0x020000
    DPAD_BOTTOM = 0x040000
    DPAD_LEFT = 0x080000
    DPAD_TOPRIGHT = 0x030000
    DPAD_BOTTOMRIGHT = 0x060000
    DPAD_BOTTOMLEFT = 0x0C0000
    DPAD_TOPLEFT = 0x090000

class StickEnum(IntEnum):
    LSTICK = 0
    RSTICK = 1

class ControllerInput(object):
    def __init__(self,action_line:str = None):
        buffer = bytearray(7)
        buffer[3] = 0x80
        buffer[4] = 0x80
        buffer[5] = 0x80
        buffer[6] = 0x80
        if action_line == None or action_line == "":
            self._buffer = buffer
            return

        splits = action_line.upper().split("|", -1)
        for s in splits:
            s = s.strip()
            if s == "Y":
                buffer[0] |= InputEnum.BUTTON_Y
            elif s == "B":
                buffer[0] |= InputEnum.BUTTON_B
            elif s == "X":
                buffer[0] |= InputEnum.BUTTON_X
            elif s == "A":
                buffer[0] |= InputEnum.BUTTON_A
            elif s == "L":
                buffer[0] |= InputEnum.BUTTON_L
            elif s == "R":
                buffer[0] |= InputEnum.BUTTON_R
            elif s == "ZL":
                buffer[0] |= InputEnum.BUTTON_ZL
            elif s == "ZR":
                buffer[0] |= InputEnum.BUTTON_ZR
            elif s == "MINUS":
                buffer[1] |= InputEnum.BUTTON_MINUS >> 8
            elif s == "PLUS":
                buffer[1] |= InputEnum.BUTTON_PLUS >> 8
            elif s == "LPRESS":
                buffer[1] |= InputEnum.BUTTON_LPRESS >> 8
            elif s == "RPRESS":
                buffer[1] |= InputEnum.BUTTON_RPRESS >> 8
            elif s == "HOME":
                buffer[1] |= InputEnum.BUTTON_HOME >> 8
            elif s == "CAPTURE":
                buffer[1] |= InputEnum.BUTTON_CAPTURE >> 8
            elif s == "TOP":
                buffer[2] |= InputEnum.DPAD_TOP >> 16
            elif s == "RIGHT":
                buffer[2] |= InputEnum.DPAD_RIGHT >> 16
            elif s == "BOTTOM":
                buffer[2] |= InputEnum.DPAD_BOTTOM >> 16
            elif s == "LEFT":
                buffer[2] |= InputEnum.DPAD_LEFT >> 16
            elif s == "TOPRIGHT":
                buffer[2] |= InputEnum.DPAD_TOPRIGHT >> 16
            elif s == "BOTTOMRIGHT":
                buffer[2] |= InputEnum.DPAD_BOTTOMRIGHT >> 16
            elif s == "BOTTOMLEFT":
                buffer[2] |= InputEnum.DPAD_BOTTOMLEFT >> 16
            elif s == "TOPLEFT":
                buffer[2] |= InputEnum.DPAD_TOPLEFT >> 16
            else:
                stick = s.split("@", -1)
                if len(stick) == 2:
                    x = 0x80
                    y = 0x80
                    coordinate = stick[1].split(",", -1)
                    if len(coordinate) == 2:
                        x = self._coordinate_str_convert_byte(coordinate[0])
                        y = self._coordinate_str_convert_byte(coordinate[1])
                    if stick[0] == "LSTICK":
                            buffer[3] = x
                            buffer[4] = y
                    elif stick[0] == "RSTICK":
                            buffer[5] = x
                            buffer[6] = y
        self._buffer = buffer

    def get_buffer(self):
        return self._buffer
    
    def check_button(self,button:InputEnum)->bool:
        int_button = int(button)
        if int_button < InputEnum.BUTTON_MINUS:
            return (self._buffer[0] & button) != 0
        elif int_button < InputEnum.DPAD_TOP:
            return (self._buffer[1] & button >> 8) != 0
        else:
            return (self._buffer[2] & button >> 16) != 0

    def set_button(self,button:InputEnum):
        int_button = int(button)
        if int_button < InputEnum.BUTTON_MINUS:
            self._buffer[0] |= button
        elif int_button < InputEnum.DPAD_TOP:
            self._buffer[1] |= button >> 8
        else:
            self._buffer[2] |= button >> 16
    
    def set_stick(self,stick:StickEnum,x:int,y:int):
        if x < -128:
            x = -128
        elif x > 127:
            x = 127
        if y < -128:
            y = -128
        elif y > 127:
            y = 127
        if stick == StickEnum.LSTICK:
            self._buffer[3] = x + 0x80
            self._buffer[4] = y + 0x80
        elif stick == StickEnum.RSTICK:
            self._buffer[5] = x + 0x80
            self._buffer[6] = y + 0x80

    def get_action_line(self)->str:
        sio = StringIO()
        if (self._buffer[0] & InputEnum.BUTTON_A) != 0:
            sio.write("A|")
        if (self._buffer[0] & InputEnum.BUTTON_B) != 0:
            sio.write("B|")
        if (self._buffer[0] & InputEnum.BUTTON_X) != 0:
            sio.write("X|")
        if (self._buffer[0] & InputEnum.BUTTON_Y) != 0:
            sio.write("Y|")
        if (self._buffer[0] & InputEnum.BUTTON_L) != 0:
            sio.write("L|")
        if (self._buffer[0] & InputEnum.BUTTON_R) != 0:
            sio.write("R|")
        if (self._buffer[0] & InputEnum.BUTTON_ZL) != 0:
            sio.write("ZL|")
        if (self._buffer[0] & InputEnum.BUTTON_ZR) != 0:
            sio.write("ZR|")
        if (self._buffer[1] & InputEnum.BUTTON_MINUS >> 8) != 0:
            sio.write("MINUS|")
        if (self._buffer[1] & InputEnum.BUTTON_PLUS >> 8) != 0:
            sio.write("PLUS|")
        if (self._buffer[1] & InputEnum.BUTTON_LPRESS >> 8) != 0:
            sio.write("LPRESS|")
        if (self._buffer[1] & InputEnum.BUTTON_RPRESS >> 8) != 0:
            sio.write("RPRESS|")
        if (self._buffer[1] & InputEnum.BUTTON_HOME >>8) != 0:
            sio.write("HOME|")
        if (self._buffer[1] & InputEnum.BUTTON_CAPTURE >> 8) != 0:
            sio.write("CAPTURE|")
        if (self._buffer[2] & InputEnum.DPAD_TOP >> 16) != 0:
            sio.write("TOP|")
        if (self._buffer[2] & InputEnum.DPAD_RIGHT >> 16) != 0:
            sio.write("RIGHT|")
        if (self._buffer[2] & InputEnum.DPAD_BOTTOM>> 16) != 0:
            sio.write("BOTTOM|")
        if (self._buffer[2] & InputEnum.DPAD_LEFT >> 16) != 0:
            sio.write("LEFT|")
        x = self._buffer[3] - 0x80
        y = self._buffer[4] - 0x80
        if x != 0 or y != 0:
            sio.write("LSTICK@{0},{1}|".format(x,y))
        x = self._buffer[5] - 0x80
        y = self._buffer[6] - 0x80
        if x != 0 or y != 0:
            sio.write("RSTICK@{0},{1}|".format(x,y))

        sio.flush()
        action = sio.getvalue()
        sio.close()
        return action

    def compare(self,other)->tuple():
        ret = (True,0,0)
        ret[0] = (ret[0] \
            and ((self._buffer[0] == other._buffer[0])) \
            and ((self._buffer[1] == other._buffer[1])) \
            and ((self._buffer[2] == other._buffer[2])))
        ret[1] = sqrt(pow(self._buffer[3] - other._buffer[3],2) + pow(self._buffer[4] - other._buffer[4],2))
        ret[2] = sqrt(pow(self._buffer[5] - other._buffer[5],2) + pow(self._buffer[6] - other._buffer[6],2))
        return ret

    def _coordinate_str_convert_byte(self, str):
        v = 0
        try:
            v = int(float(str))
        except:
            pass
        if v < -128:
            v = -128
        elif v > 127:
            v = 127
        return v + 0x80