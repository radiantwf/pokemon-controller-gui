from enum import Enum
import multiprocessing
import time
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
from recognition.scripts.games.pokemon.champions.teamid.team import Team


class ChampoinsTeamID(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(ChampoinsTeamID.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, ChampoinsTeamID.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False
        self._teamid_form_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/teamid_form.png", cv2.IMREAD_GRAYSCALE)
        self._team = Team()
        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._teamid = self.get_para("teamid")

    @staticmethod
    def script_name() -> str:
        return "宝可梦-Champoins-识别租借队伍"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["loop"] = ScriptParameter(
            "loop", int, 1, "运行次数")
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["teamid"] = ScriptParameter(
            "teamid", str, "ULUG3FD87Y", "队伍ID")
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
        self._check_pokemon_index = -1
        self.send_log(f"开始运行{ChampoinsTeamID.script_name()}脚本")

    def on_cycle(self):
        if self.cycle_times > 0 and self.cycle_times % 5 == 0:
            run_time_span = self.run_time_span
            log_txt = ""
            log_txt += f"[{ChampoinsTeamID.script_name()}] 脚本运行中，已运行{self.cycle_times}次，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                                                           3600) / 60)}分{int(run_time_span % 60)}秒"
            self.send_log(log_txt)
        self._check_pokemon_index = -1

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(ChampoinsTeamID.script_name(
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
            self.step_3,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        # self.macro_run("common.switch_sleep",
        #                loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(ChampoinsTeamID.script_name(), self.cycle_times - 1, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        pass

    def _cycle_init(self):
        pass

    def step_0(self):
        self.macro_run("recognition.pokemon.champions.team_id.enter_teamid_form",
                       loop=1, paras={}, block=True)
        self.macro_run("common.input_text_by_qwer",
                       loop=1, paras={"input_text": str(self._teamid)}, block=True)
        time.sleep(3)
        self._jump_next_frame = True
        self._cycle_step_index += 1

    def step_1(self):
        current_frame = self.current_frame
        if not self._check_teamid_form(current_frame):
            self.macro_run("common.press_button_b",
                           loop=-1, paras={}, block=True, timeout=12)
            self._re_cycle()
            return
        self._cycle_step_index += 1

    def step_2(self):
        current_frame = self.current_frame
        self.macro_text_run("R:0.1\n1", loop=1, block=False)
        self._team.process_moves_image(current_frame)
        self._jump_next_frame = True
        self._cycle_step_index += 1

    def step_3(self):
        current_frame = self.current_frame
        self._team.process_states_image(current_frame)
        
        # 复制str(self._team)至电脑剪切版
        try:
            import pyperclip
            pyperclip.copy(str(self._team))
            self.send_log("已将队伍信息复制到剪贴板")
        except ImportError:
            self.send_log("未安装 pyperclip，无法复制到剪贴板，请运行 pip install pyperclip")
        except Exception as e:
            self.send_log(f"复制到剪贴板失败: {e}")

        self._cycle_step_index += 1

    def _check_teamid_form(self, image):
        crop_x, crop_y, crop_w, crop_h = 531, 201, 853, 47
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._teamid_form_template, cv2.TM_CCOEFF_NORMED)
        _, max_val1, _, _ = cv2.minMaxLoc(match)
        if max_val1 >= 0.9:
            return True
        return False