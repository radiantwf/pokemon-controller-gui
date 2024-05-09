from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2


class SWSHDAStart(BaseSubStep):
    def __init__(self, script: BaseScript, choose_record: int = 1, save_record: int = 1, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._choose_record_index = choose_record
        self._save_record_index = save_record
        self._initial_chat_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/initial_chat.png")
        self._initial_chat_template = cv2.cvtColor(
            self._initial_chat_template, cv2.COLOR_BGR2GRAY)
        self._dynamax_adventures_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/dynamax_adventures_label.png")
        self._dynamax_adventures_template = cv2.cvtColor(
            self._dynamax_adventures_template, cv2.COLOR_BGR2GRAY)
        self._dynamax_adventures_quit_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/dynamax_adventures_quit.png")
        self._dynamax_adventures_quit_template = cv2.cvtColor(
            self._dynamax_adventures_quit_template, cv2.COLOR_BGR2GRAY)
        self._choose_record_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/choose_fight_record.png")
        self._choose_record_template = cv2.cvtColor(
            self._choose_record_template, cv2.COLOR_BGR2GRAY)
        self._save_record_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/save_fight_record.png")
        self._save_record_template = cv2.cvtColor(
            self._save_record_template, cv2.COLOR_BGR2GRAY)

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
            self._process_step_2,
            self._process_step_3,
        ]

    def _process_step_0(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_save_record(gray_frame):
            print(f"Save Record: {self._save_record_index}")
            if self._save_record_index == 1:
                self.script.macro_text_run("A:0.1", block=True)
            elif self._save_record_index == 2:
                self.script.macro_text_run(
                    "BOTTOM:0.1->0.3->A:0.1", block=True)
            elif self._save_record_index == 3:
                self.script.macro_text_run(
                    "BOTTOM:0.1->0.3->BOTTOM:0.1->0.3->A:0.1", block=True)
            else:
                self.script.macro_text_run("B:0.1", block=True)
            self.time_sleep(0.4)
            return
        if self._match_initial_chat(gray_frame):
            self._process_step_index += 1
            return
        self.script.macro_text_run("A:0.1", block=True)
        self.time_sleep(0.4)

    def _process_step_1(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_dynamax_adventures(gray_frame):
            self.time_sleep(1)
            self._process_step_index += 1
            return
        if self._match_choose_record(gray_frame):
            if self._choose_record_index == 1:
                self.script.macro_text_run("A:0.1", block=True)
            elif self._choose_record_index == 2:
                self.script.macro_text_run(
                    "BOTTOM:0.1->0.3->A:0.1", block=True)
            elif self._choose_record_index == 3:
                self.script.macro_text_run(
                    "BOTTOM:0.1->0.3->BOTTOM:0.1->0.3->A:0.1", block=True)
            else:
                self.script.macro_text_run("B:0.1", block=True)
            self.time_sleep(0.4)
            return
        self.script.macro_text_run(
            "A:0.1", block=True)
        self.time_sleep(0.5)

    def _process_step_2(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_dynamax_adventures_quit(gray_frame):
            self.script.macro_text_run("B:0.1", block=True)
            self.time_sleep(1)
            self._process_step_index = 1
            return
        self.script.macro_text_run("BOTTOM:0.1->0.4->A:0.1->0.4", block=True)
        self.time_sleep(2)
        self._process_step_index += 1

    def _process_step_3(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_dynamax_adventures_quit(gray_frame):
            self.script.macro_text_run("B:0.1", block=True)
            self.time_sleep(1)
            self._process_step_index = 1
            return
        self.script.macro_text_run("A:0.1", block=True)
        self.time_sleep(1)
        self._process_step_index += 1

    def _process_step_4(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_dynamax_adventures_quit(gray_frame):
            self.script.macro_text_run("B:0.1", block=True)
            self.time_sleep(1)
            self._process_step_index = 1
            return
        self.script.macro_text_run("A:0.1", block=True)
        self.time_sleep(18)
        self._process_step_index += 1

    def _match_initial_chat(self, gray, threshold=0.9) -> bool:
        crop_x, crop_y, crop_w, crop_h = 160, 431, 636, 95
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._initial_chat_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold

    def _match_dynamax_adventures(self, gray, threshold=0.9) -> bool:
        crop_x, crop_y, crop_w, crop_h = 0, 0, 570, 95
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._dynamax_adventures_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold

    def _match_dynamax_adventures_quit(self, gray, threshold=0.9) -> bool:
        crop_x, crop_y, crop_w, crop_h = 561, 362, 365, 46
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._dynamax_adventures_quit_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold

    def _match_choose_record(self, gray, threshold=0.9) -> bool:
        crop_x, crop_y, crop_w, crop_h = 643, 378, 154, 70
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._choose_record_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
    
    def _match_save_record(self, gray, threshold=0.9) -> bool:
        crop_x, crop_y, crop_w, crop_h = 159, 378, 639, 149
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._save_record_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
