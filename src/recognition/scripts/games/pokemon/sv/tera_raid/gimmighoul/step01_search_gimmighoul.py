import time
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2

from recognition.scripts.games.pokemon.sv.common.image_match.map_N_match import MapNIconMatch


class SVGimmighoulSearch(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._begin_time = None
        self._end_time = None
        self._last_raid_text_match_ts = None
        self._five_star_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/raid/five_star.jpg", cv2.IMREAD_GRAYSCALE)
        self._gimmighoul_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/raid/gimmighoul.jpg", cv2.IMREAD_GRAYSCALE)
        self._raid_text_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/raid/raid_text.jpg", cv2.IMREAD_GRAYSCALE)

    def _process(self) -> SubStepRunningStatus:
        if self._begin_time is None:
            self._begin_time = time.monotonic()
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

    @property
    def run_time_span(self):
        if self._begin_time is None:
            return 0
        if self._end_time is None:
            return time.monotonic() - self._begin_time
        return self._end_time - self._begin_time

    def _process_step_0(self):
        self.script.macro_run("pokemon.sv.raid.refresh_raid",
                              1, {}, True, None)
        # self.script.macro_text_run("B:0.1->0.4", loop=4, block=True)
        self.time_sleep(2)
        self._process_step_index += 1

    def _process_step_1(self):
        if self._last_raid_text_match_ts is not None and time.monotonic() - self._last_raid_text_match_ts > 300:
            self._status = SubStepRunningStatus.Failed
            return
        # current_frame_960x480 = self.script.current_frame_960x480
        # gray_frame = cv2.cvtColor(current_frame_960x480, cv2.COLOR_BGR2GRAY)
        # is_match = MapNIconMatch().match_map_N_icon_template(gray_frame)
        # if not is_match:
        #     self.script.send_log("未检测到右下角小地图N图标，无法继续")
        #     self._status = SubStepRunningStatus.Failed
        #     return
        self.script.macro_text_run("A:0.1->0.05", loop=2, block=True)
        self.time_sleep(2)
        self._raid_text_match_times = 0
        self._process_step_index += 1

    def _process_step_2(self):
        current_frame_960x480 = self.script.current_frame_960x480
        gray_frame = cv2.cvtColor(current_frame_960x480, cv2.COLOR_BGR2GRAY)
        is_match = self._match_raid_text_template(gray_frame)
        if not is_match:
            if self._raid_text_match_times < 2:
                self._raid_text_match_times += 1
                return
            self._process_step_index = 0
            return
        self._last_raid_text_match_ts = time.monotonic()
        is_match = self._match_gimmighoul_template(gray_frame)
        if not is_match:
            self._process_step_index += 1
            return
        is_match = self._match_five_star_template(gray_frame)
        if not is_match:
            self._process_step_index += 1
            return
        self._status = SubStepRunningStatus.OK
        self._end_time = time.monotonic()

    def _process_step_3(self):
        # self.script.save_temp_image()
        self.script.macro_text_run("B:0.1->0.4", loop=5, block=True)
        self._process_step_index = 0

    def _match_gimmighoul_template(self, gray, threshold=0.9) -> bool:
        rect = (625, 205, 70, 85)
        crop_gray = gray[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        res = cv2.matchTemplate(
            crop_gray, self._gimmighoul_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold

    def _match_five_star_template(self, gray, threshold=0.9) -> bool:
        rect = (560, 300, 200, 40)
        crop_gray = gray[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        res = cv2.matchTemplate(
            crop_gray, self._five_star_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # print(max_val)
        # if max_val >= 0.1:
        #     self.script.save_temp_image(rect)
        return max_val >= threshold

    def _match_raid_text_template(self, gray, threshold=0.7) -> bool:
        rect = (140, 90, 160, 35)
        crop_gray = gray[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        res = cv2.matchTemplate(
            crop_gray, self._raid_text_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # print(max_val)
        # if max_val >= 0.1:
        #     self.script.save_temp_image(rect)
        return max_val >= threshold
