import multiprocessing
import time
from recognition.scripts.base import BaseScript, WorkflowEnum
import cv2
import numpy as np


class SwshBattleShiny(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        super().__init__(SwshBattleShiny.script_name(), stop_event, frame_queue, controller_input_action_queue)
        self._prepare_steps = self.init_prepare_steps()
        self._prepare_step_index = -1
        self._circle_steps = self.init_circle_steps()
        self._circle_step_index = -1
        self._template = cv2.imread("resources/img/battle_shiny.jpg")
        self._template = cv2.cvtColor(self._template, cv2.COLOR_BGR2GRAY)
        self._template_p = (865,430)

    @staticmethod
    def script_name()->str:
        return "剑盾定点刷闪"

    def process_frame(self):
        if self.running_status ==  WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0 and self._prepare_step_index < len(self._prepare_steps):
                self._prepare_steps[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._circle_step_index >= 0 and self._circle_step_index < len(self._circle_steps):
                self._circle_steps[self._circle_step_index]()
            else:
                self.set_circle_continue()
                self._circle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCircle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0

    def on_stop(self):
        pass

    def on_error(self):
        pass

    def init_prepare_steps(self):
        return [
            self.prepare_step_0,
        ]
    def prepare_step_0(self):
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
        self._circle_step_2_start_time_monotonic = 0
        self._circle_step_2_time_monotonic_check_1 = 0
        self._circle_step_2_frame_count_check_1 = 0
        pass

    def circle_step_0(self):
        if self.current_frame_count == 1:
            self.macro_run("pokemon.swsh.common.restart_game",1,{},True,None)
            self._circle_step_index += 1
        else:
            self.macro_stop()
            self.set_circle_continue()
            self._circle_step_index = 0

    def circle_step_1(self):
        self.macro_run("pokemon.common.press_button_a",-1,{},False,None)
        self._circle_step_index += 1

    def circle_step_2(self):
        if self._circle_step_2_start_time_monotonic == 0:
            self._circle_step_2_start_time_monotonic = time.monotonic()

        if time.monotonic() - self._circle_step_2_start_time_monotonic > 60:
            self._circle_step_index += 1
            return

        image = self.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(gray, self._template, cv2.TM_CCOEFF_NORMED)
        _,max_val,_,p=cv2.minMaxLoc(match)
        if max_val > 0.75 and abs(p[0] - self._template_p[0])<=10 and abs(p[1] - self._template_p[1])<=10:
            if self._circle_step_2_time_monotonic_check_1 == 0:
                self._circle_step_2_time_monotonic_check_1 = time.monotonic()
                self._circle_step_2_frame_count_check_1 = self.current_frame_count
                self.macro_stop(block=False)
            else:
                span = time.monotonic() - self._circle_step_2_time_monotonic_check_1
                if span <= 0.15:
                    return
                elif span < 2:
                    self._circle_step_index += 1
                    return
                elif span < 3:
                    self.macro_stop()
                    self.send_log("请检查是否有闪光")
                    self.stop_work()

    def circle_step_3(self):
        self.macro_stop()
        self.set_circle_continue()
        self._circle_step_index = 0

    # async def run(self):
    #     last_span_frame_count = 0
    #     span_second = 0
    #     _start_monotonic = time.monotonic()
    #     _frame_count = 0
    #     self._enable_send_action = True
    #     await self.send_action(macro.macro_close_game,1)
    #     await asyncio.sleep(1)
    #     await self.send_action(macro.macro_press_button_a_loop,1)
    #     macro_run = True
    #     while True:
    #         if time.monotonic() - _start_monotonic > 60 and self._enable_send_action:
    #             await self.send_action(macro.macro_close_game,1)
    #             await asyncio.sleep(1)
    #             await self.send_action(macro.macro_press_button_a_loop,1)
    #             _start_monotonic = time.monotonic()
    #             macro_run = True
    #             _frame_count = 0

    #         data = await self._frame.get_frame()
    #         image = (
    #             np
    #             .frombuffer(data, np.uint8)
    #             .reshape([self._frame.height, self._frame.width, 3])
    #         )
    #         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #         match = cv2.matchTemplate(gray, self._template, cv2.TM_CCOEFF_NORMED)
    #         _,max_val,_,p=cv2.minMaxLoc(match)
    #         if max_val > 0.75 and abs(p[0] - self._template_p[0])<=10 and abs(p[1] - self._template_p[1])<=10:
    #             if macro_run:
    #                 await self.send_action(macro.macro_action_clear,1)
    #                 macro_run = False
    #             if time.monotonic() - _start_monotonic > 0.15 and _frame_count>0:
    #                 last_span_frame_count = _frame_count
    #                 span_second = time.monotonic() - _start_monotonic
    #             _frame_count=0
    #             _start_monotonic = time.monotonic()
    #             x = p[0] +  self._template.shape[0] - 1
    #             y = p[1] +  self._template.shape[1] - 1
    #             if y >= self._frame.height:
    #                 x = self._frame.height - 1
    #             if y >= self._frame.width:
    #                 x = self._frame.width - 1
    #             image = cv2.rectangle(image, p, (x,y), (0, 255, 0), 4, 4)
    #         else:
    #             _frame_count += 1
            
    #         if span_second < 3 and span_second > 0.15 and last_span_frame_count > 0:
    #             img = Image.fromarray(image)
    #             draw = ImageDraw.Draw(img)
    #             draw.text((40, 50), "间隔时间：{:.3f}秒".format(span_second), (0, 255, 0), font=self._fontText)
    #             draw.text((40, 82), "{:d}帧".format(last_span_frame_count), (0, 255, 0), font=self._fontText)
    #             image = np.asarray(img)
    #         try:
    #             self._opencv_processed_video_frame.put(image.tobytes(),False,0)
    #         except:
    #             pass

    #         if span_second < 2 and span_second > 0.15 and last_span_frame_count > 0 and not macro_run:
    #             if span_second < 0.7:
    #                 await self.send_action(macro.macro_close_game,1)
    #                 await asyncio.sleep(1)
    #                 await self.send_action(macro.macro_press_button_a_loop,1)
    #                 macro_run = True
    #             else:
    #                 await self.send_action(macro.macro_action_clear,1)
    #                 macro_run = False
    #                 self._enable_send_action = False