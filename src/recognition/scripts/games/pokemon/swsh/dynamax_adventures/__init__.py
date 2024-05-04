from enum import Enum
import multiprocessing
import time
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step01_start import SWSHDAStart
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step02_choose_path import SWSHDAChoosePath
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step03_battle import SWSHDABattle, SWSHDABattleResult
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step04_catch import SWSHDACatch, SWSHDACatchResult
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step05_switch_pokemon import SWSHDASwitchPokemon
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step06_shiny_keep import SWSHDAShinyKeep, SWSHDAShinyKeepResult
from recognition.scripts.games.pokemon.swsh.dynamax_adventures.step07_finish import SWSHDAFinish
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


class SWSHDAWhenRestart(Enum):
    Never = "不重启"
    NotShiny_And_WonLegendary = "未闪光，击败传说宝可梦重启(寻找最佳路线，保留过程闪光宝可梦)"
    NotShinyLegendary_And_WonLegendary = "传说未闪光，击败传说宝可梦重启(寻找最佳路线)"
    NotShinyLegendary = "传说宝可梦未闪光重启(已确认最佳路线)"
    NotShiny = "没有闪光宝可梦未重启(已确认最佳路线、保留过程闪光宝可梦)"


TRACE_LOG = False


class SwshDynamaxAdventures(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(SwshDynamaxAdventures.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, SwshDynamaxAdventures.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False

        self._shiny_count = 0
        self._win_count = 0
        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._secondary = self.get_para(
            "secondary") if "secondary" in paras else False
        self._use_record = self.get_para(
            "use_record") if "use_record" in paras else 1
        self._save_record = self.get_para(
            "save_record") if "save_record" in paras else 1
        self._not_keep_restart_flag = self.get_para(
            "not_keep_restart") if "not_keep_restart" in paras else SWSHDAWhenRestart.Never.value
        self._only_keep_legendary = self.get_para(
            "only_keep_legendary") if "only_keep_legendary" in paras else False
        self._choose_path = [self.get_para("choose_path_1") if "choose_path_1" in paras else 0,
                             self.get_para(
                                 "choose_path_2") if "choose_path_2" in paras else 0,
                             self.get_para("choose_path_3") if "choose_path_3" in paras else 0]
        self._path_enter_event = [True,
                                  self.get_para(
                                      "path_enter_event_2") if "path_enter_event_2" in paras else True,
                                  self.get_para(
                                      "path_enter_event_3") if "path_enter_event_3" in paras else True,
                                  self.get_para("path_event_4") if "path_event_4" in paras else True]
        self._path_leave_event = [True, self.get_para("path_leave_event_2") if "path_leave_event_2" in paras else True,
                                  self.get_para("path_leave_event_3") if "path_leave_event_3" in paras else True]
        self._catch_ball = [self.get_para("catch_ball_1") if "catch_ball_1" in paras else SWSHDABallType.PokeBall.value,
                            self.get_para(
                                "catch_ball_2") if "catch_ball_2" in paras else SWSHDABallType.PokeBall.value,
                            self.get_para(
                                "catch_ball_3") if "catch_ball_3" in paras else SWSHDABallType.PokeBall.value,
                            self.get_para("catch_ball_4") if "catch_ball_4" in paras else SWSHDABallType.BeastBall.value]
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
        paras["loop"] = ScriptParameter(
            "loop", int, -1, "运行次数")
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["only_keep_legendary"] = ScriptParameter(
            "only_keep_legendary", bool, "False", "只带走传说宝可梦", ["False", "True"])
        paras["not_keep_restart"] = ScriptParameter(
            "not_keep_restart", str, SWSHDAWhenRestart.NotShiny_And_WonLegendary.value, "重启游戏选项（有极巨石惩罚）", [e.value for e in SWSHDAWhenRestart])
        paras["secondary"] = ScriptParameter(
            "secondary", bool, "False", "副设备", ["False", "True"])

        paras["use_record"] = ScriptParameter(
            "use_record", int, 1, "使用记录（0:不使用 1-3:使用记录1-3）", ["1", "2", "3", "0"])
        paras["save_record"] = ScriptParameter(
            "save_record", int, 1, "保存并覆盖原有记录（0:不保存 1-3:覆盖记录位置1-3）", ["1", "2", "3", "0"])

        paras["choose_path_1"] = ScriptParameter(
            "choose_path_1", int, 0, "战斗1 选择路径（0:默认路径，负数:向左移动，正数:向右移动，数字:移动次数）")
        paras["catch_ball_1"] = ScriptParameter(
            "catch_ball_1", str, SWSHDABallType.PokeBall.value, "战斗1 捕捉球种", [e.value for e in SWSHDABallType])
        paras["switch_pokemon_1"] = ScriptParameter(
            "switch_pokemon_1", bool, "True", "战斗1 是否更换使用宝可梦（未捕捉跳过此步骤）", ["False", "True"])

        paras["choose_path_2"] = ScriptParameter(
            "choose_path_2", int, 0, "战斗2 选择路径（0:默认路径，负数:向左移动，正数:向右移动，数字:移动次数）")
        paras["path_enter_event_2"] = ScriptParameter(
            "path_enter_event_2", bool, "True", "战斗2 进入战斗路径事件（True:连点A False:连点B）", ["False", "True"])
        paras["catch_ball_2"] = ScriptParameter(
            "catch_ball_2", str, SWSHDABallType.PokeBall.value, "战斗2 捕捉球种", [e.value for e in SWSHDABallType])
        paras["switch_pokemon_2"] = ScriptParameter(
            "switch_pokemon_2", bool, "True", "战斗2 是否更换使用宝可梦（未捕捉跳过此步骤）", ["False", "True"])
        paras["path_leave_event_2"] = ScriptParameter(
            "path_leave_event_2", bool, "True", "战斗2 离开战斗路径事件（True:连点A False:连点B）", ["False", "True"])

        paras["choose_path_3"] = ScriptParameter(
            "choose_path_3", int, 0, "战斗3 选择路径（0:默认路径，负数:向左移动，正数:向右移动，数字:移动次数）")
        paras["path_enter_event_3"] = ScriptParameter(
            "path_enter_event_3", bool, "True", "战斗3 进入战斗路径事件（True:连点A False:连点B）", ["False", "True"])
        paras["catch_ball_3"] = ScriptParameter(
            "catch_ball_3", str, SWSHDABallType.PokeBall.value, "战斗3 捕捉球种", [e.value for e in SWSHDABallType])
        paras["switch_pokemon_3"] = ScriptParameter(
            "switch_pokemon_3", bool, "True", "战斗3 是否更换使用宝可梦（未捕捉跳过此步骤）", ["False", "True"])
        paras["path_leave_event_3"] = ScriptParameter(
            "path_leave_event_3", bool, "True", "战斗2 离开战斗路径事件（True:连点A False:连点B）", ["False", "True"])

        paras["catch_ball_4"] = ScriptParameter(
            "catch_ball_4", str, SWSHDABallType.BeastBall.value, "BOSS战 捕捉球种", [e.value for e in SWSHDABallType])
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
        self.send_log(f"开始运行{SwshDynamaxAdventures.script_name()}脚本")

    def on_cycle(self):
        run_time_span = self.run_time_span
        self.send_log("脚本运行中，已经运行{}次，成功攻略大冒险{}次，带回闪光宝可梦{}只，耗时{}小时{}分{}秒".format(self.cycle_times, self._win_count,
                      self._shiny_count, int(run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，成功攻略大冒险{}次，带回闪光宝可梦{}只，耗时{}小时{}分{}秒".format(SwshDynamaxAdventures.script_name(
        ), self.cycle_times, self._win_count, self._shiny_count, int(run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

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
        self.macro_run("common.switch_sleep",
                       loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(SwshDynamaxAdventures.script_name(), self.cycle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        self.macro_stop()
        self.set_cycle_continue()
        self._cycle_step_index = 0
        self._battle_index = 0
        self._legendary_caught = False
        self._swsh_da_start = SWSHDAStart(
            self, save_record=self._save_record, choose_record=self._use_record, timeout=90)
        self._swsh_da_choose_path = None
        self._swsh_da_battle = None
        self._swsh_da_catch = None
        self._swsh_da_switch_pokemon = None
        self._swsh_da_shiny_keep = None
        self._swsh_da_finish = SWSHDAFinish(self)

    def _cycle_init(self):
        self._battle_index = 0
        self._legendary_caught = False
        self._swsh_da_start = SWSHDAStart(
            self, save_record=self._save_record, choose_record=self._use_record, timeout=90)
        self._swsh_da_choose_path = None
        self._swsh_da_battle = None
        self._swsh_da_catch = None
        self._swsh_da_switch_pokemon = None
        self._swsh_da_shiny_keep = None
        self._swsh_da_finish = SWSHDAFinish(self)

    def step_1_start(self):
        status = self._swsh_da_start.run()
        if status == SubStepRunningStatus.Running:
            return
        # elif status == SubStepRunningStatus.Failed:
        # elif status == SubStepRunningStatus.Timeout:
        # elif status == SubStepRunningStatus.Finished:
        elif status == SubStepRunningStatus.OK:
            self._swsh_da_choose_path = SWSHDAChoosePath(
                self, True, True, battle_index=self._battle_index, path=self._choose_path[self._battle_index],)
            self._cycle_step_index += 1
            if TRACE_LOG:
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
            self._cycle_step_index += 1
            if TRACE_LOG:
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
                if self._battle_index >= 3:
                    self._legendary_caught = True
                catch_flag = (
                    self._catch_ball[self._battle_index] != SWSHDABallType.NotCatch.value)
                self._swsh_da_catch = SWSHDACatch(
                    self, battle_index=self._battle_index, catch=catch_flag, target_ball=self._catch_ball[self._battle_index])
                self._cycle_step_index += 1
                if TRACE_LOG:
                    self.send_log("胜利，准备捕捉")
                return
            if self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost3:
                self._re_cycle()
                if TRACE_LOG:
                    self.send_log("失败3，重启开始下一轮大冒险")
                return
            if self._not_keep_restart_flag == SWSHDAWhenRestart.NotShinyLegendary.value:
                if TRACE_LOG:
                    self.send_log("未击败传说宝可梦，重启开始下一轮大冒险")
                self.macro_run("recognition.pokemon.swsh.common.restart_game",
                               1, {"secondary": str(self._secondary)}, True, None)
                self._re_cycle()
                return
            if self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost1:
                self._cycle_step_index = 5
                self._swsh_da_shiny_keep = SWSHDAShinyKeep(
                    self, only_keep_legendary=self._only_keep_legendary, legendary_caught=self._legendary_caught)
                if TRACE_LOG:
                    self.send_log("失败1，带走宝可梦")
                return
            elif self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost2:
                self._cycle_step_index = 6
                if TRACE_LOG:
                    self.send_log("失败2，准备结束")
                return
            elif self._swsh_da_battle.battle_status == SWSHDABattleResult.Lost3:
                self._re_cycle()
                if TRACE_LOG:
                    self.send_log("失败3，重启开始下一轮大冒险")
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
                if self._legendary_caught:
                    self._cycle_step_index = 5
                    self._swsh_da_shiny_keep = SWSHDAShinyKeep(
                        self, only_keep_legendary=self._only_keep_legendary, legendary_caught=self._legendary_caught)
                    self._win_count += 1
                    if TRACE_LOG:
                        self.send_log("传说宝可梦捕捉成功")
                    return
                else:
                    switch_flag = self._switch_pokemon[self._battle_index]
                    self._swsh_da_switch_pokemon = SWSHDASwitchPokemon(
                        self, battle_index=self._battle_index, switch=switch_flag)
                    self._cycle_step_index += 1
                    if TRACE_LOG:
                        self.send_log("捕捉成功，准备切换宝可梦")
            else:
                self._battle_index += 1
                self._swsh_da_choose_path = SWSHDAChoosePath(
                    self, leave_event=self._path_leave_event[self._battle_index - 1], enter_event=self._path_enter_event[self._battle_index], battle_index=self._battle_index, path=self._choose_path[self._battle_index],)
                self._cycle_step_index = 1
                if TRACE_LOG:
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
                self, leave_event=self._path_leave_event[self._battle_index - 1], enter_event=self._path_enter_event[self._battle_index], battle_index=self._battle_index, path=0,)
            self._cycle_step_index = 1
            if TRACE_LOG:
                self.send_log("切换宝可梦成功，准备重新选择路径")
            return
        else:
            self.send_log("{}函数返回状态为{}".format(
                "swsh_da_switch_pokemon", status.name))
            self._finished_process()

    def step_6_shiny_keep(self):
        status = self._swsh_da_shiny_keep.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            if self._swsh_da_shiny_keep.kept_result == SWSHDAShinyKeepResult.KeptLegendary:
                self._shiny_count += 1
                self.send_log("检测到传说宝可梦闪光，请手动确认")
                self._finished_process()
                return
            if self._swsh_da_shiny_keep.kept_result == SWSHDAShinyKeepResult.Kept:
                if self._not_keep_restart_flag == SWSHDAWhenRestart.NotShinyLegendary_And_WonLegendary.value and self._legendary_caught:
                    self.send_log("成功击败传说宝可梦，传说宝可梦未闪光（已忽略其他闪光宝可梦），重启开始下一轮大冒险")
                    self.macro_run("recognition.pokemon.swsh.common.restart_game",
                                   1, {"secondary": str(self._secondary)}, True, None)
                    self._re_cycle()
                    return
                self.send_log("非传说闪光宝可梦保留成功")
                self._shiny_count += 1
                self._cycle_step_index += 1
                return
            if TRACE_LOG:
                self.send_log("未检测到闪光宝可梦")

            if self._not_keep_restart_flag == SWSHDAWhenRestart.NotShiny.value:
                self.send_log("未检测到闪光宝可梦，重启开始下一轮大冒险")
                self.macro_run("recognition.pokemon.swsh.common.restart_game",
                               1, {"secondary": str(self._secondary)}, True, None)
                self._re_cycle()
                return
            if (self._not_keep_restart_flag == SWSHDAWhenRestart.NotShiny_And_WonLegendary.value or self._not_keep_restart_flag == SWSHDAWhenRestart.NotShinyLegendary_And_WonLegendary.value) and self._legendary_caught:
                self.send_log("成功击败传说宝可梦，未检测到闪光宝可梦，重启开始下一轮大冒险")
                self.macro_run("recognition.pokemon.swsh.common.restart_game",
                               1, {"secondary": str(self._secondary)}, True, None)
                self._re_cycle()
                return
            self._cycle_step_index += 1
            return
        else:
            self.send_log("{}函数返回状态为{}".format(
                "swsh_da_shiny_keep", status.name))
            self._finished_process()

    def step_7_finish(self):
        status = self._swsh_da_finish.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            self._cycle_step_index += 1
            return
        else:
            self.send_log("{}函数返回状态为{}".format(
                "swsh_da_finish", status.name))
            self._finished_process()
