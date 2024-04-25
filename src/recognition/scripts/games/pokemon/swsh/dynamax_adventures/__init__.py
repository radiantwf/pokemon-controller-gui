from enum import Enum
import multiprocessing
import time
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step01_start import SWSHDAStart
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step02_choose_path import SWSHDAChoosePath
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step03_battle import SWSHDABattle, SWSHDABattleResult
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step04_catch import SWSHDACatch, SWSHDACatchResult
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step05_switch_pokemon import SWSHDASwitchPokemon
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
from recognition.scripts.base.base_sub_step import SubStepRunningStatus


class SWSHDABallType(Enum):
    NotCatch = "不捕捉"
    PokeBall = "精灵球"
    GreatBall = "超级球"
    UltraBall = "高级球"
    MasterBall = "大师球"
    SafariBall = "狩猎球"
    LevelBall = "等级球"
    MoonBall = "月亮球"
    LureBall = "诱饵球"
    FriendBall = "友友球"
    LoveBall = "甜蜜球"
    FastBall = "速度球"
    HeavyBall = "重量球"
    PremierBall = "纪念球"
    RepeatBall = "重复球"
    TimerBall = "计时球"
    NestBall = "巢穴球"
    NetBall = "捕网球"
    DiveBall = "潜水球"
    LuxuryBall = "豪华球"
    HealBall = "治愈球"
    QuickBall = "先机球"
    DuskBall = "黑暗球"
    SportBall = "竞赛球"
    DreamBall = "梦境球"
    BeastBall = "究极球"


class SwshDynamaxAdventures(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(SwshDynamaxAdventures.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, SwshDynamaxAdventures.script_paras())
        self._prepare_step_index = -1
        self._circle_step_index = -1
        self._jump_next_frame = False
        self.set_paras(paras)
        self._battle_index = 0

        # 获取脚本参数
        self._durations = self.get_para("durations")
        self._restart_game = self.get_para(
            "restart_game") if "restart_game" in paras else False
        self._only_take_legendary = self.get_para(
            "only_take_legendary") if "only_take_legendary" in paras else False
        self._choose_path = [self.get_para("choose_path_1") if "choose_path_1" in paras else 0,
                             self.get_para(
                                 "choose_path_2") if "choose_path_2" in paras else 0,
                             self.get_para("choose_path_3") if "choose_path_3" in paras else 0]
        self._path_event = [self.get_para("path_event_1") if "path_event_1" in paras else True,
                            self.get_para(
                                "path_event_2") if "path_event_2" in paras else True,
                            self.get_para(
                                "path_event_3") if "path_event_3" in paras else True,
                            self.get_para("path_event_4") if "path_event_4" in paras else True]
        self._catch_ball = [self.get_para("catch_ball_1") if "catch_ball_1" in paras else SWSHDABallType.PokeBall,
                            self.get_para(
                                "catch_ball_2") if "catch_ball_2" in paras else SWSHDABallType.PokeBall,
                            self.get_para(
                                "catch_ball_3") if "catch_ball_3" in paras else SWSHDABallType.PokeBall,
                            self.get_para("catch_ball_4") if "catch_ball_4" in paras else SWSHDABallType.BeastBall]
        self._switch_pokemon = [self.get_para("switch_pokemon_1") if "switch_pokemon_1" in paras else True,
                                self.get_para(
                                    "switch_pokemon_2") if "switch_pokemon_2" in paras else True,
                                self.get_para("switch_pokemon_3") if "switch_pokemon_3" in paras else True]

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
            self.step_1_start,
            self.step_2_choose_path,
            self.step_3_battle,
            self.step_4_catch,
            self.step_5_switch_pokemon,
            self.step_6_shiny_keep,
            self.step_7_finish,
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
        self._swsh_da_switch_pokemon = None

    def step_1_start(self):
        status = self._swsh_da_start.run()
        if status == SubStepRunningStatus.Running:
            return
        # elif status == SubStepRunningStatus.Failed:
        # elif status == SubStepRunningStatus.Timeout:
        # elif status == SubStepRunningStatus.Finished:
        elif status == SubStepRunningStatus.OK:
            self._swsh_da_choose_path = SWSHDAChoosePath(
                self, battle_index=self._battle_index)
            self._circle_step_index += 1
            self.send_log("开始选择路径")
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_start", status.name))
            self._finished_process()

    def step_2_choose_path(self):
        status = self._swsh_da_choose_path.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            self._swsh_da_battle = SWSHDABattle(
                self, battle_index=self._battle_index)
            self._circle_step_index += 1
            self.send_log("选择路径完成，准备战斗")
        else:
            self.send_log("{}函数返回状态为{}".format(
                "swsh_da_choose_path", status.name))
            self._finished_process()

    def step_3_battle(self):
        status = self._swsh_da_battle.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("swsh_da_battle", status.name))
            self._finished_process()
        elif status == SubStepRunningStatus.OK:
            if self._swsh_da_battle.battle_status == SWSHDABattleResult.Won:
                catch_flag = (
                    self._catch_ball[self._battle_index] != SWSHDABallType.NotCatch)
                self._swsh_da_catch = SWSHDACatch(
                    self, battle_index=self._battle_index, catch=catch_flag, target_ball=self._catch_ball[self._battle_index].value)
                self._circle_step_index += 1
                self.send_log("胜利，准备捕捉")
                return
            elif self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost1:
                self._circle_step_index = 5
                self.send_log("失败1，带走宝可梦")
                return
            elif self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost2:
                self._circle_step_index = 6
                self.send_log("失败2，准备结束")
                return
            elif self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost3:
                self._circle_step_index = 6
                self.send_log("失败3，准备结束")
                return
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_battle", status.name))
            self._finished_process()

    def step_4_catch(self):
        status = self._swsh_da_catch.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format("swsh_da_catch", status.name))
            self._finished_process()
        elif status == SubStepRunningStatus.OK:
            if self._swsh_da_catch.catch_result == SWSHDACatchResult.Caught:
                if self._battle_index >= 3:
                    self._circle_step_index = 5
                    self.send_log("捕捉成功，准备结束")
                else:
                    switch_flag = self._switch_pokemon[self._battle_index]
                    self._swsh_da_switch_pokemon = SWSHDASwitchPokemon(
                        self, battle_index=self._battle_index, switch=switch_flag)
                    self._circle_step_index += 1
                    self.send_log("捕捉成功，准备切换宝可梦")
            else:
                self._battle_index += 1
                self._swsh_da_choose_path = SWSHDAChoosePath(
                    self, battle_index=self._battle_index)
                self._circle_step_index = 1
                self.send_log("未捕捉，准备重新选择路径")
            return
        else:
            self.send_log("{}函数返回状态为{}".format("swsh_da_catch", status.name))
            self._finished_process()

    def step_5_switch_pokemon(self):
        status = self._swsh_da_switch_pokemon.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.Timeout:
            self.send_log("{}函数返回状态为{}".format(
                "swsh_da_switch_pokemon", status.name))
            self._finished_process()
        elif status == SubStepRunningStatus.OK:
            self._battle_index += 1
            self._swsh_da_choose_path = SWSHDAChoosePath(
                self, battle_index=self._battle_index)
            self._circle_step_index = 1
            self.send_log("切换宝可梦成功，准备重新选择路径")
            return
        else:
            self.send_log("{}函数返回状态为{}".format(
                "swsh_da_switch_pokemon", status.name))
            self._finished_process()

    def step_6_shiny_keep(self):
        self._finished_process()

    def step_7_finish(self):
        self._finished_process()
