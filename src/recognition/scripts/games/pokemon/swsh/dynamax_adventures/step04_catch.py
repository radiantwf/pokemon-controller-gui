from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import time
import cv2
import numpy as np
import pytesseract


class SWSHDACatch(BaseSubStep):
    def __init__(self, script: BaseScript,  target_ball: str = "究极球", timeout: float = 60) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._target_ball = target_ball

    def _process(self) -> SubStepRunningStatus:
        self._status = self.running_status
        if self._process_step_index >= 0:
            if self._process_step_index >= len(self._process_steps):
                return SubStepRunningStatus.OK
            elif self._status == SubStepRunningStatus.Running:
                self._process_steps[self._process_step_index]()
                return self._status
            else:
                return self._status
        else:
            self._process_step_index = 0
            return self._process()

    @property
    def _process_steps(self):
        return [
            self._process_step_0,
            self._process_step_1,
        ]

    def _process_step_0(self):
        self.script.macro_text_run("A:0.1", block=True)
        self.time_sleep(0.5)
        self._last_action_time_monotonic = time.monotonic()
        self._initial_ball = None
        self._process_step_index += 1

    def _process_step_1(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        # 识别球种
        current_ball = self._ocr_current_ball(gray_frame)
        num = self._ocr_current_ball_left_num(gray_frame)
        print(current_ball, num)
        if current_ball == "":
            return
        else:
            if self._initial_ball is None:
                self._initial_ball = current_ball
            elif current_ball == self._initial_ball:
                self._target_ball = None
                self._initial_ball = "不检测"

            catch_flag = False
            if self._target_ball is None:
                catch_flag = (self._alternatives(current_ball) and num > 1)
            else:
                if current_ball == self._target_ball and num > 1:
                    catch_flag = True
            if catch_flag:
                self.script.macro_text_run("A:0.1", block=True)
                self.time_sleep(8)
                self._last_action_time_monotonic = time.monotonic()
                self._process_step_index += 1
            else:
                self.script.macro_text_run("RIGHT:0.1", block=True)
                self.time_sleep(0.5)
                self._last_action_time_monotonic = time.monotonic()

    def _ocr_current_ball(self, gray):
        crop_x, crop_y, crop_w, crop_h = 726, 336, 68, 30
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*5, crop_h*5))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(
            crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        kernel = np.ones((6, 6), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=精灵球超级高大师纪念治愈捕网巢穴潜水黑暗计时先机重复豪华速度友诱饵等级沉重甜蜜月亮梦境竞赛究极狩猎'
        text = pytesseract.image_to_string(
            closing, lang='chi_sim', config=custom_config)
        text = "".join(text.split())
        if text == "精球":
            text = "精灵球"
        elif text == "治球":
            text = "治愈球"
        elif text == "愈球":
            text = "治愈球"
        elif text == "潜球":
            text = "巢穴球"
        elif text == "球":
            text = "巢穴球"
        elif text == "暗球":
            text = "黑暗球"
        elif text == "华球":
            text = "豪华球"
        elif text == "重球":
            text = "沉重球"
        elif text == "境球":
            text = "梦境球"
        elif text == "饵球":
            text = "诱饵球"
        return text

    def _ocr_current_ball_left_num(self, gray):
        crop_x, crop_y, crop_w, crop_h = 879, 342, 37, 21
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*5, crop_h*5))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(
            crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        kernel = np.ones((6, 6), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        text = pytesseract.image_to_string(closing, config=custom_config)
        text = "".join(text.split())
        num = int(text) if text.isdigit() else 0
        return num

    def _alternatives(self, ball):
        if ball == "精灵球":
            return True
        elif ball == "豪华球":
            return True
        else:
            return False
