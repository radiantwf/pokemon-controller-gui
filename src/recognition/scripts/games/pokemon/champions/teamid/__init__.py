import multiprocessing
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future, CancelledError
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
from recognition.scripts.games.pokemon.champions.teamid.team import Team
from recognition.scripts.games.pokemon.champions.teamid.output import (
    _normalize_rental_codes, _new_log_path, append_process_log,
    create_pokepaste_until_success,
)


MAX_ASYNC_WORKERS = 3


class ChampionsTeamID(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(ChampionsTeamID.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, ChampionsTeamID.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False
        self._teamid_form_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/teamid_form.png", cv2.IMREAD_GRAYSCALE)
        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._teamids = _normalize_rental_codes(self.get_para("teamid"))
        self._code_index = 0
        self._processed_count = 0
        self._log_path = None
        self._offsets_y = 0
        self._moves_frame = None
        self._capture_count = 0
        self._capture_done = False
        self._executor = None
        self._pending_tasks = deque()
        self._async_stop_event = threading.Event()
        # BaseScript clears _stop_event before on_stop; workers need a stable reference.
        self._batch_stop_event = stop_event

    @staticmethod
    def script_name() -> str:
        return "宝可梦-Champions-识别租借队伍(中文)"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["teamid"] = ScriptParameter(
            "teamid", str, "", "队伍ID（每行一个，可用逗号分隔）", multiline=True)
        paras["loop"] = ScriptParameter(
            "loop", int, 1, "运行次数（整批）")
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
        if not self._capture_done:
            return False
        if not self._pending_tasks:
            self._finished_process()
        return True

    def process_frame(self):
        self._flush_completed_results()
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
        self.send_log(f"开始运行{ChampionsTeamID.script_name()}脚本")
        if not self._teamids:
            self.send_log("租借码列表为空，脚本停止")
            self.stop_work()
            return
        self._log_path = _new_log_path(self._teamids)
        self._log_path.write_text("", encoding="utf-8")
        self.send_log(f"批量日志文件: {self._log_path}")
        self._executor = ThreadPoolExecutor(max_workers=MAX_ASYNC_WORKERS)

    def on_cycle(self):
        if self.cycle_times > 0 and self.cycle_times % 5 == 0:
            run_time_span = self.run_time_span
            log_txt = ""
            log_txt += f"[{ChampionsTeamID.script_name()}] 脚本运行中，已运行{self.cycle_times}次，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                                                           3600) / 60)}分{int(run_time_span % 60)}秒"
            self.send_log(log_txt)
        self._check_pokemon_index = -1

    def on_stop(self):
        self._shutdown_background()
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(ChampionsTeamID.script_name(
        ), self.cycle_times, int(run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        self.send_log(f"租借队伍处理异常，已输出结果保存在: {self._log_path}")

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
        self._shutdown_background()
        # self.macro_run("common.switch_sleep",
        #                loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒\n--------------------------------------------".format(ChampionsTeamID.script_name(), self._processed_count, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        if self._log_path is not None:
            self.send_log(f"批量日志文件: {self._log_path}")
        self.stop_work()

    def _re_cycle(self):
        self._cycle_step_index = 0

    def _cycle_init(self):
        pass

    @property
    def _rental_code(self):
        return self._teamids[self._code_index]

    def _background_should_stop(self):
        return (
            self._async_stop_event.is_set()
            or (self._batch_stop_event is not None and self._batch_stop_event.is_set())
            or (self._durations > 0 and self.run_time_span >= self._durations * 60)
        )

    def _process_images(self, rental_code, moves_frame, states_frame, offsets_y, output_dir, save_images):
        team = None
        try:
            if self._background_should_stop():
                raise InterruptedError
            team = Team(offsets_y, output_dir=output_dir, save_images=save_images,
                        should_stop=self._background_should_stop)
            team.process_moves_image(moves_frame)
            if self._background_should_stop():
                raise InterruptedError
            team.process_states_image(states_frame)
            if self._background_should_stop():
                raise InterruptedError
            target_url = create_pokepaste_until_success(
                str(team), title=f"OCR Team {rental_code}", author="OCR",
                stop_event=self._async_stop_event,
                should_stop=self._background_should_stop,
                send_log=self.send_log,
            )
            return team, target_url, None
        except InterruptedError:
            return team, None, f"租借码 {rental_code} 后台处理已停止"
        except Exception as error:
            return team, None, f"租借码 {rental_code} 后台处理失败: {error}"

    def _flush_completed_results(self):
        # Only the capture thread writes results, always in submission/input order.
        while self._pending_tasks and self._pending_tasks[0][1].done():
            rental_code, future = self._pending_tasks[0]
            try:
                team, target_url, error = future.result()
            except CancelledError:
                team, target_url, error = None, None, f"租借码 {rental_code} 后台处理已取消"
            except Exception as exception:
                team, target_url, error = None, None, f"租借码 {rental_code} 后台处理失败: {exception}"
            section = append_process_log(self._log_path, rental_code, team, target_url, error=error)
            self._pending_tasks.popleft()
            self._processed_count += 1
            print(section)
            self.send_log(section)

    def _shutdown_background(self):
        self._async_stop_event.set()
        if self._executor is not None:
            self._executor.shutdown(wait=True, cancel_futures=True)
            self._executor = None
        self._flush_completed_results()

    def _advance_capture(self):
        self._capture_count += 1
        self._code_index = (self._code_index + 1) % len(self._teamids)
        self._moves_frame = None
        self._cycle_step_index = len(self._cycle_step_list)
        if self._loop > 0 and self._capture_count >= self._loop * len(self._teamids):
            self._capture_done = True
            self.send_log("截图读取完成，等待后台识别和上传结束")
            return
        self.macro_run("common.press_button_b", loop=-1, paras={}, block=True, timeout=12)
        self._jump_next_frame = True

    def step_0(self):
        self._moves_frame = None
        self.send_log(f"开始读取租借码: {self._rental_code}")
        self.macro_run("recognition.pokemon.champions.team_id.enter_teamid_form",
                       loop=1, paras={}, block=True)
        self.macro_run("common.input_text_by_qwer",
                       loop=1, paras={"input_text": self._rental_code}, block=True)
        time.sleep(3)
        self._jump_next_frame = True
        self._cycle_step_index += 1

    def step_1(self):
        if not self._check_teamid_form(self.current_frame):
            future = Future()
            future.set_result((None, None, f"租借码 {self._rental_code} 未检测到队伍详情页面"))
            self._pending_tasks.append((self._rental_code, future))
            self._flush_completed_results()
            self._advance_capture()
            return
        self._cycle_step_index += 1

    def step_2(self):
        self._moves_frame = self.current_frame.copy()
        self.macro_text_run("R:0.1\n1", loop=1, block=True)
        self._jump_next_frame = True
        self._cycle_step_index += 1

    def step_3(self):
        rental_code = self._rental_code
        # Snapshot both images and the offset before navigating to the next rental code.
        states_frame = self.current_frame.copy()
        # Repeated single-code runs use separate folders to prevent concurrent image writes.
        output_dir = "./outputs"
        if len(self._teamids) == 1 and self._loop != 1:
            output_dir = f"./outputs/capture_{self._capture_count}"
        future = self._executor.submit(
            self._process_images, rental_code, self._moves_frame, states_frame,
            self._offsets_y, output_dir, len(self._teamids) == 1,
        )
        self._pending_tasks.append((rental_code, future))
        self.send_log(f"已提交后台处理: {rental_code}")
        self._advance_capture()

    def _check_teamid_form(self, image):
        crop_x, crop_y, crop_w, crop_h = 531, 181, 853, 97
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._teamid_form_template, cv2.TM_CCOEFF_NORMED)
        _, max_val1, _, p = cv2.minMaxLoc(match)
        if max_val1 >= 0.9:
            self._offsets_y = p[1]-20
            return True
        return False
