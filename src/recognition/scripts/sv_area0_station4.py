import math
import multiprocessing
import time
from recognition.scripts.base import BaseScript, WorkflowEnum
import cv2
import numpy as np


class SVArea0Station4(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        super().__init__(SVArea0Station4.script_name(), stop_event,
                         frame_queue, controller_input_action_queue)
        self._prepare_steps = self.init_prepare_steps()
        self._prepare_step_index = -1
        self._circle_steps = self.init_circle_steps()
        self._circle_step_index = -1
        self._template = None
        # self._template = cv2.imread("resources/img/area0_station4.jpg")
        # self._template = cv2.cvtColor(self._template, cv2.COLOR_BGR2GRAY)
        self._template_p = (0, 280)

    @staticmethod
    def script_name() -> str:
        return "朱紫0号区4号站路闪"

    def process_frame(self):
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0 and self._prepare_step_index < len(self._prepare_steps):
                self._prepare_steps[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._circle_step_index >= 0 and self._circle_step_index < len(self._circle_steps):
                self._circle_steps[self._circle_step_index]()
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
        self.send_log("开始运行宝可梦朱紫0号区4号站路闪图像识别检测脚本")

    def on_circle(self):
        if self.circle_times > 0 and self.circle_times % 10 == 0:
            run_time_span = self.run_time_span
            self.send_log("闪光检测中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, math.floor(
                run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format('宝可梦剑盾定点闪图像识别检测脚本', self.circle_times, math.floor(
            run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))

    def on_error(self):
        pass

    def init_prepare_steps(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        img = self.current_frame
        img = img[self._template_p[1]: self._template_p[1] + 130,
                    self._template_p[0]: self._template_p[0] + 960]
        cv2.imwrite("resources/img/area0_station4.jpg", img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self._template = img
        self.set_circle_begin()
        self._circle_step_index = 0

    def init_circle_steps(self):
        return [
            self.circle_step_0,
            self.circle_step_1,
            self.circle_step_2,
            self.circle_step_3,
        ]

    def circle_init(self):
        self.last_capture_time = 0
        pass

    def circle_step_0(self):
        self.macro_run("recognition.pokemon.sv.area0.area0_station4",
                       1, {}, False, None)
        self._bg_frame = None
        self._bg_frame_blur = None
        self._circle_step_index += 1

    def circle_step_1(self):
        # img = self.current_frame
        # cv2.imshow('Video', img)
        # cv2.waitKey(1)
        if self.current_circle_time_span >= 20:
            img = self.current_frame
            cv2.imwrite("./Captures/{}-{}.jpg".format(time.strftime(
                "%Y%m%d%H%M%S", time.localtime()), self.current_frame_count), self.current_frame)
            self._circle_step_index += 1
            return
        if self.current_circle_time_span >= 4.0 and self.macro_running:
            img = self.current_frame
            img = img[self._template_p[1]: self._template_p[1] + self._template.shape[0],
                      self._template_p[0]: self._template_p[0] + self._template.shape[1]]
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            match = cv2.matchTemplate(
                img, self._template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, p = cv2.minMaxLoc(match)
            if max_val > 0.4:
                # print(max_val, self.current_frame_count,
                #     self.current_circle_time_span)
                self.macro_stop(block=False)
            return
        if not self.macro_running and self.current_circle_time_span >= 4.0:
            img = self.current_frame
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self._bg_frame is None:
                self._bg_frame = img
                self._bg_frame_blur = cv2.GaussianBlur(img, (21, 21), 0)
            else:
                frame_blur = cv2.GaussianBlur(img, (21, 21), 0)
                # 计算背景图像和当前帧图像的差分图像
                diff = cv2.absdiff(self._bg_frame_blur, frame_blur)
                # 对差分图像进行二值化处理
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                cv2.imshow('Video', thresh)
                cv2.waitKey(1)
        pass

    def circle_step_2(self):
        self._circle_step_index += 1
        pass

    def circle_step_3(self):
        self._circle_step_index += 1
        pass
