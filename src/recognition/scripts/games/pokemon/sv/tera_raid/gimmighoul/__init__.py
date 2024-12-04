from enum import Enum
import multiprocessing
import time

from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
from recognition.scripts.base.base_sub_step import SubStepRunningStatus
from recognition.scripts.games.pokemon.sv.tera_raid.gimmighoul.step01_search_gimmighoul import SVGimmighoulSearch
from recognition.scripts.games.pokemon.sv.tera_raid.gimmighoul.step02_battle import SVGimmighoulBattle
from recognition.scripts.games.pokemon.sv.tera_raid.gimmighoul.step03_pokedex import SVGimmighoulPokedex, SVPokedexShinyMatchResult
from recognition.scripts.parameter_struct import ScriptParameter

TRACE_LOG = False


class SvTeraRaidGimmighoul(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(SvTeraRaidGimmighoul.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, SvTeraRaidGimmighoul.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False
        self._step2_retries = 0
        self._step2_retries_limit = 2

        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._secondary = self.get_para(
            "secondary") if "secondary" in paras else False
        self._find_target_times = 0


    @staticmethod
    def script_name() -> str:
        return "宝可梦朱紫刷闪坑"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["loop"] = ScriptParameter(
            "loop", int, -1, "运行次数")
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

    def _check_cycles(self):
        if self._loop <= 0:
            return False
        if self.cycle_times > self._loop:
            self.send_log("运行次数已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False

    def process_frame(self):
        if self._check_durations():
            return
        if self._check_cycles():
            return

        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self._prepare_step_list):
                    self.set_cycle_begin()
                    self._cycle_step_index = 0
                    return
                self._prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Cycle:
            if self.current_frame_count == 1:
                self._cycle_init()
            if self._jump_next_frame:
                self.clear_frame_queue()
                self._jump_next_frame = False
                return
            if self._cycle_step_index >= 0 and self._cycle_step_index < len(self._cycle_step_list):
                self._cycle_step_list[self._cycle_step_index]()
            else:
                self.macro_stop()
                self.set_cycle_continue()
                self._cycle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCycle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self._find_target_times = 0
        self.send_log(f"开始运行{SvTeraRaidGimmighoul.script_name()}脚本")

    def on_cycle(self):
        run_time_span = self.run_time_span
        log_txt = ""
        log_txt += f"[{SvTeraRaidGimmighoul.script_name()}] 脚本运行中，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                                    3600) / 60)}分{int(run_time_span % 60)}秒"
        self.send_log(log_txt)

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(SvTeraRaidGimmighoul.script_name(
        ), self.cycle_times, int(run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

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
            self.step_0,
            self.step_1,
            self.step_2,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(SvTeraRaidGimmighoul.script_name(), self.cycle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        self.sv_tera_raid_gimmighoul_search = SVGimmighoulSearch(self)
        self.sv_battle = SVGimmighoulBattle(self)
        self.sv_pokedex = SVGimmighoulPokedex(self)
        self._step2_retries = 0


    def _cycle_init(self):
        self.sv_tera_raid_gimmighoul_search = SVGimmighoulSearch(self)
        self.sv_battle = SVGimmighoulBattle(self)
        self.sv_pokedex = SVGimmighoulPokedex(self)
        self._step2_retries = 0

    def step_0(self):
        self.sv_tera_raid_gimmighoul_search.run()
        status = self.sv_tera_raid_gimmighoul_search.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            timespan = self.sv_tera_raid_gimmighoul_search.run_time_span
            self._find_target_times += 1
            self.send_log(
                f'第{self._find_target_times}次找到目标巢穴，本次耗时{int((timespan % 3600) / 60)}分{int(timespan % 60)}秒')
        else:
            self.send_log("{}函数返回状态为{}".format(
                "sv_tera_raid_gimmighoul_search", status.name))
            self._finished_process()
        self._cycle_step_index += 1

    def step_1(self):
        self.sv_battle.run()
        status = self.sv_battle.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            self._cycle_step_index += 1
            return
        else:
            self.send_log("{}函数返回状态为{}".format(
                "sv_battle", status.name))
            self._finished_process()

    def step_2(self):
        self.sv_pokedex.run()
        status = self.sv_pokedex.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            if self.sv_pokedex.result == SVPokedexShinyMatchResult.Shiny:
                self._cycle_step_index += 1
                self.send_log("找到目标闪光宝可梦")
                self._finished_process()
                return
            self.send_log("目标宝可梦未闪光")
            self._cycle_step_index += 1
            return
        elif status == SubStepRunningStatus.Timeout:
            if self._step2_retries >= self._step2_retries_limit:
                self.send_log("{}函数返回状态为{}".format(
                "sv_pokedex", status.name))
                self._finished_process()
            self.send_log("图鉴校验超时，重新校验")
            self.script.macro_text_run("B:0.1->0.4", loop=5, block=True)
            self.time_sleep(0.5)
            self._step2_retries += 1
            self.sv_pokedex = SVGimmighoulPokedex(self)
            return
        else:
            self.send_log("{}函数返回状态为{}".format(
                "sv_pokedex", status.name))
            self._finished_process()
