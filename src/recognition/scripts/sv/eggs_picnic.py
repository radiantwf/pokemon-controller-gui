import math
import multiprocessing
import time
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
import numpy as np


class SVEggsPicnic(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        super().__init__(SVEggsPicnic.script_name(), stop_event,
                         frame_queue, controller_input_action_queue)
        self._prepare_step_index = -1
        self._circle_step_index = -1
        self._jump_next_frame = False
        self._menu_arrow_template = cv2.imread("resources/img/recognition/pokemon/sv/menu_arrow.jpg")
        self._menu_arrow_template = cv2.cvtColor(self._menu_arrow_template, cv2.COLOR_BGR2GRAY)
    @staticmethod
    def script_name() -> str:
        return "宝可梦朱紫野餐取蛋"

    def process_frame(self):
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self.prepare_step_list):
                    self.set_circle_begin()
                    self._circle_step_index = 0
                    return
                self.prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._jump_next_frame:
                self._jump_next_frame = False
                return
            if self._circle_step_index >= 0 and self._circle_step_index < len(self.cycle_step_list):
                self.cycle_step_list[self._circle_step_index]()
            else:
                self.macro_stop()
                self.set_circle_continue()
                self._circle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCircle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self.send_log(f"开始运行{SVEggsPicnic.script_name()}脚本")

    def on_circle(self):
        pass
        # run_time_span = self.run_time_span
        # self.send_log("脚本运行中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, int(
        #     run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(SVEggsPicnic.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    @property
    def prepare_step_list(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self._prepare_step_index += 1

    @property
    def cycle_step_list(self):
        return [
            self.picnic,
        ]

    def circle_init(self):
        self.picnic_step_index = 0
        pass

    def picnic(self):
        if self.picnic_step_index >= 0:
            if self.picnic_step_index >= len(self.picnic_step_list):
                self._circle_step_index += 1
                return
            self.picnic_step_list[self.picnic_step_index]()
        else:
            self.picnic_step_index = 0
            self.picnic()

    # 包包 0.9837725162506104 (648, 121)
    # 盒子 0.9873440265655518 (649, 161)            
    # 野餐 0.9854351282119751 (648, 201)
    # 宝可入口站 0.9781053066253662 (648, 241)
    # 设置 0.9854401350021362 (648, 281)
    # 记录 0.9784520864486694 (648, 321)
    # 付费新增内容 0.9627913236618042 (649, 419)

    # 宝可梦1 0.9802355170249939 (23, 91)
    # 宝可梦2 0.9705981016159058 (23, 154)
    # 宝可梦3 0.9855178594589233 (23, 217)
    # 宝可梦4 0.9850992560386658 (23, 280)
    # 宝可梦5 0.9853918552398682 (23, 343)
    # 宝可梦6 0.9780521988868713 (23, 406)
    # 坐骑 0.9853339195251465 (23, 491)


    @property
    def picnic_step_list(self):
        return [
            self.picnic_0,
            self.picnic_1,
            self.picnic_2,
            self.picnic_3,
        ]

    # 返回初始状态
    def picnic_0(self):
        # 连续点击B 持续2秒
        self.macro_text_run("B:0.1\n0.1", loop=10, block=True)
        self.picnic_step_index += 1

    # 打开菜单
    def picnic_1(self):
        self.macro_text_run("X", block=True)
        self._picnic_open_menu_ts = time.monotonic()
        self.picnic_step_index += 1
    
    
    # 检测菜单栏是否打开，与光标所在位置
    def picnic_2(self):
        if time.monotonic() - self._picnic_open_menu_ts < 0.5:
            return
        image = self.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(gray, self._menu_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        
        if max_val < 0.9:
            self.picnic_step_index = 0
            return
        if p[0] < 600:
            self.macro_text_run("Right", block=True)
            time.sleep(0.5)
            self._jump_next_frame = True
            return
        if p[1] < 190 or p[1] > 310:
            self.macro_text_run("Bottom", block=True)
            time.sleep(0.1)
            self._jump_next_frame = True
            return
        if p[1] > 210:
            self.macro_text_run("Top", block=True)
            time.sleep(0.1)
            self._jump_next_frame = True
            return
        self.picnic_step_index += 1
        
    def picnic_3(self):
        self.macro_run("recognition.pokemon.sv.eggs.picnic_3", -1, {}, True, None)
        self.picnic_step_index += 1

    def hatching(self):
        self.stop_work()
        self._circle_step_index += 1

    def release(self):
        self._circle_step_index += 1
