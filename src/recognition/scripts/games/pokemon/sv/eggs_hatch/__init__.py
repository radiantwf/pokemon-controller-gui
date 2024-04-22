import math
import multiprocessing
import time
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
import numpy as np
from recognition.scripts.base.base_sub_step import SubStepRunningStatus
from recognition.scripts.games.pokemon.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.games.pokemon.sv.common.menu.enter_item import SVEnterMenuItem, SVMenuItems

from recognition.scripts.games.pokemon.sv.common.menu.open import SVOpenMenu
from recognition.scripts.games.pokemon.sv.eggs_hatch.box_opt import SVBoxOptPokemon
from recognition.scripts.games.pokemon.sv.eggs_hatch.hatch import SVHatchPokemon


class SVEggs(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict() = None):
        super().__init__(SVEggs.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, SVEggs.script_paras())
        self._prepare_step_index = -1
        self._circle_step_index = -1
        self._jump_next_frame = False
        self.set_paras(paras)
        self._durations = self.get_para("durations")
        SVBoxOptPokemon.initial()

    @staticmethod
    def script_name() -> str:
        return "宝可梦朱紫孵蛋"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        return paras
    
    def check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self.finished_process()
            return True
        return False
        
    def process_frame(self):
        if self.check_durations():
            return
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
        self.send_log(f"开始运行{SVEggs.script_name()}脚本")

    def on_circle(self):
        pass
        # run_time_span = self.run_time_span
        # self.send_log("脚本运行中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, int(
        #     run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(SVEggs.script_name(), self.circle_times, int(
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
            self.step_1_open_menu,
            self.step_2_enter_box,
            self.step_3_box_opt,
            self.step_4_hatch,
        ]

    def circle_init(self):
        self._sv_open_menu = SVOpenMenu(self)
        self._sv_enter_menu_box = SVEnterMenuItem(
            self, menu_item=SVMenuItems.Box)
        self._sv_box_opt = SVBoxOptPokemon(self)
        self.hatching_step_index = 0
        pass

    def step_1_open_menu(self):
        status = self._sv_open_menu.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Failed:
            self.send_log("{}函数返回状态为{}".format("open_menu", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("open_menu", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Finished:
            self.finished_process()
            return
        elif status == SubStepRunningStatus.OK:
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("open_menu", status.name))
            self.finished_process()

    def step_2_enter_box(self):
        status = self._sv_enter_menu_box.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Failed:
            self.send_log("{}函数返回状态为{}".format("enter_box", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("enter_box", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Finished:
            self.finished_process()
            return
        elif status == SubStepRunningStatus.OK:
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("enter_box", status.name))
            self.finished_process()

    def step_3_box_opt(self):
        status = self._sv_box_opt.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Failed:
            self.send_log("{}函数返回状态为{}".format("box_opt", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("box_opt", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Finished:
            self.finished_process()
            return
        elif status == SubStepRunningStatus.OK:
            image = self.current_frame
            eggs = BoxMatch().current_party_eggs(image)
            if eggs <= 0:
                self._circle_step_index = 0
                return
            self._sv_hatch_opt = SVHatchPokemon(self, eggs)
            self._circle_step_index += 1
        else:
            self.send_log("{}函数返回状态为{}".format("box_opt", status.name))
            self.finished_process()

    def step_4_hatch(self):
        status = self._sv_hatch_opt.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Failed:
            self.send_log("{}函数返回状态为{}".format("hatch", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("hatch", status.name))
            self.re_circle()
        elif status == SubStepRunningStatus.Finished:
            self.finished_process()
            return
        elif status == SubStepRunningStatus.OK:
            self.re_circle()
        else:
            self.send_log("{}函数返回状态为{}".format("hatch", status.name))
            self.finished_process()

    def finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(SVEggs.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def re_circle(self):
        self.macro_stop()
        self.set_circle_continue()
        self._circle_step_index = 0
