
from recognition.scripts.base.base_sub_step import BaseSubStep

def move_cursor(self: BaseSubStep, current: tuple[int, int], move_target: tuple[int, int]):
    x = move_target[0] - current[0]
    y = move_target[1] - current[1]
    if x == 0 and y == 0:
        return
    while x != 0 or y != 0:
        if move_target[0] == 0:
            if x > 0:
                self.script.macro_text_run("RIGHT:0.05\n0.05", block=True)
                x -= 1
            elif x < 0:
                self.script.macro_text_run("LEFT:0.05\n0.05", block=True)
                x += 1
            elif y > 0:
                self.script.macro_text_run("BOTTOM:0.05\n0.05", block=True)
                y -= 1
            elif y < 0:
                self.script.macro_text_run("TOP:0.05\n0.05", block=True)
                y += 1
        else:
            if y > 0:
                self.script.macro_text_run("BOTTOM:0.05\n0.05", block=True)
                y -= 1
            elif y < 0:
                self.script.macro_text_run("TOP:0.05\n0.05", block=True)
                y += 1
            elif x > 0:
                self.script.macro_text_run("RIGHT:0.05\n0.05", block=True)
                x -= 1
            elif x < 0:
                self.script.macro_text_run("LEFT:0.05\n0.05", block=True)
                x += 1
