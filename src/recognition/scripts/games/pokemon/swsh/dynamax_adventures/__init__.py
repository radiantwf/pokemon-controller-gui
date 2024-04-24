import math
import multiprocessing
import time
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step01_start import SWSHDAStart
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step02_choose_path import SWSHDAChoosePath
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step03_battle import SWSHDABattle
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step04_catch import SWSHDACatch
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
import numpy as np
from recognition.scripts.base.base_sub_step import SubStepRunningStatus



class SwshDynamaxAdventures(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict() = None):
        super().__init__(SwshDynamaxAdventures.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, SwshDynamaxAdventures.script_paras())
        self._prepare_step_index = -1
        self._circle_step_index = -1
        self._jump_next_frame = False
        self.set_paras(paras)
        self._durations = self.get_para("durations")


    @staticmethod
    def script_name() -> str:
        return "宝可梦剑盾极巨大冒险(开发中)"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        return paras
    
    def _check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False
        
    def process_frame(self):
        if self._check_durations():
            return
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self._prepare_step_list):
                    self.set_circle_begin()
                    self._circle_step_index = 0
                    return
                self._prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self._circle_init()
            if self._jump_next_frame:
                self._jump_next_frame = False
                return
            if self._circle_step_index >= 0 and self._circle_step_index < len(self._cycle_step_list):
                self._cycle_step_list[self._circle_step_index]()
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
        self.send_log(f"开始运行{SwshDynamaxAdventures.script_name()}脚本")

    def on_circle(self):
        pass
        # run_time_span = self.run_time_span
        # self.send_log("脚本运行中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, int(
        #     run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(SwshDynamaxAdventures.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    @property
    def _prepare_step_list(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self._prepare_step_index += 1

    @property
    def _cycle_step_list(self):
        return [
            # self.step_1,
            self.step_2,
            self.step_3,
            self.step_4,
            self.step_5,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        # self.macro_run("common.switch_sleep",
        #                loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(SwshDynamaxAdventures.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_circle(self):
        self.macro_stop()
        self.set_circle_continue()
        self._circle_step_index = 0

    def _circle_init(self):
        self._swsh_da_start = SWSHDAStart(self)
        self._swsh_da_choose_path = None
        self._swsh_da_battle = None
        self._swsh_da_catch = None
        
    def step_1(self):
        status = self._swsh_da_start.run()
        if status == SubStepRunningStatus.Running:
            return
        # elif status == SubStepRunningStatus.Failed:
        # elif status == SubStepRunningStatus.Timeout:
        # elif status == SubStepRunningStatus.Finished:
        elif status == SubStepRunningStatus.OK:
            self._swsh_da_choose_path = SWSHDAChoosePath(self)
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_start", status.name))
            self._finished_process()
            
    def step_2(self):
        # status = self._swsh_da_choose_path.run()
        status = SubStepRunningStatus.OK
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            self._swsh_da_battle = SWSHDABattle(self)
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_choose_path", status.name))
            self._finished_process()

    def step_3(self):
        status = self._swsh_da_battle.run()
        if status == SubStepRunningStatus.Running:
            return
        # elif status == SubStepRunningStatus.Failed:
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("swsh_da_battle", status.name))
            self._finished_process()
        # elif status == SubStepRunningStatus.Finished:
        elif status == SubStepRunningStatus.OK:
            self._swsh_da_catch = SWSHDACatch(self)
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_battle", status.name))
            self._finished_process()
    
    def step_4(self):
        status = self._swsh_da_catch.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("swsh_da_catch", status.name))
            self._finished_process()
        elif status == SubStepRunningStatus.OK:
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_catch", status.name))
            self._finished_process()

    def step_5(self):
        self._finished_process()