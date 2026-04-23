import multiprocessing
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
from recognition.scripts.games.pokemon.champions.usage.pokemon import Pokemon, DetailTagEnum
from recognition.scripts.games.pokemon.champions.usage.recognize import Recognize
import time

_detail_worker_local = threading.local()


def _get_detail_worker_recognize():
    recognize = getattr(_detail_worker_local, "recognize", None)
    if recognize is None:
        recognize = Recognize()
        _detail_worker_local.recognize = recognize
    return recognize


def _recognize_detail_row_async(current_frame, detail_tag, top_clipped, row_index):
    recognize = _get_detail_worker_recognize()
    return recognize.recognize_detail_row(current_frame, detail_tag, top_clipped, row_index)


class ChampionsUsage(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(ChampionsUsage.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, ChampionsUsage.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False
        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._currentPokemonRank = self.get_para("start")
        self._ns1 = self.get_para("ns1") if paras and "ns1" in paras else False

        self._output_path = Path("outputs/usage.json.text")

        self._recognize = Recognize()
        self._detail_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="usage-detail")
        self._pokemon = None
        self._last_pokemon_flg = False

    @staticmethod
    def script_name() -> str:
        return "宝可梦-Champions-宝可梦使用率(中文)"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["start"] = ScriptParameter(
            "start", int, 1, "起始位置")
        paras["loop"] = ScriptParameter(
            "loop", int, -1, "运行次数")
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["ns1"] = ScriptParameter(
            "ns1", bool, False, "是否使用NS1")
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
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        if self._currentPokemonRank == 1:
            self._output_path.write_text("", encoding="utf-8")
        self.send_log(f"开始运行{ChampionsUsage.script_name()}脚本")

    def on_cycle(self):
        if self.cycle_times > 0 and self.cycle_times % 5 == 0:
            run_time_span = self.run_time_span
            log_txt = ""
            log_txt += f"[{ChampionsUsage.script_name()}] 脚本运行中，已运行{self.cycle_times}次，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                                                          3600) / 60)}分{int(run_time_span % 60)}秒"
            self.send_log(log_txt)
        self._check_pokemon_index = -1

    def on_stop(self):
        self._detail_executor.shutdown(wait=True, cancel_futures=False)
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(ChampionsUsage.script_name(
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
        self.macro_run("recognition.pokemon.champions.usage.enter_usage_form",
                       loop=1, paras={}, block=True)
        if self._currentPokemonRank < 1:
            self._currentPokemonRank = 1
        if self._currentPokemonRank > 1:
            self.macro_text_run("LStick@0,127:0.1\n0.4", loop=self._currentPokemonRank-1, block=True)
        self._jump_next_frame = True

    @property
    def _cycle_step_list(self):
        return [
            self.step_0,
            self.step_1_1,
            self.step_1_2,
            self.step_1_3,
            self.step_2,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(ChampionsUsage.script_name(), self.cycle_times - 1, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        self._cycle_step_index = 0

    def _cycle_init(self):
        pass

    def step_0(self):
        current_frame = self.current_frame
        name, self._last_pokemon_flg = self._recognize.recognize_pokemon(current_frame, self._currentPokemonRank)
        self._pokemon = Pokemon(self._currentPokemonRank, name)

        self.macro_text_run("1\nA:0.1\n2\nLStick@0,-127:0.15\n0.4\nLStick@0,-127:0.15\n0.4\nLStick@0,-127:0.15\n0.4\nLStick@0,-127:0.15\n0.8", loop=1, block=True)
        self._jump_next_frame = True
        self._detail_tag = DetailTagEnum.Move
        self._detail_index = 0

        # self.macro_run("recognition.pokemon.champions.team_id.enter_Usage_form",
        #                loop=1, paras={}, block=True)
        # self.macro_run("common.input_text_by_qwer",
        #                loop=1, paras={"input_text": str(self._Usage)}, block=True)
        # time.sleep(3)
        # self._jump_next_frame = True
        self._cycle_step_index += 1

    def step_1_1(self):
        self._detail_rows = 0
        current_frame = self.current_frame
        top_clipped = self._recognize.check_detail_top_clipped(current_frame)
        for i in range(5):
            rows = self._recognize.recognize_detail_row_rank(current_frame, self._detail_tag, top_clipped, 4-i)
            if rows > 0:
                break
        if rows > 0:
            self._detail_rows = rows
            self._left_rows = rows
            self._detail_tmp_dict = {}
        else:
            raise Exception("未识别到有效数据")
        print(f'总行数:{rows}')
        self._cycle_step_index += 1

    def step_1_2(self):
        current_frame = self.current_frame.copy()

        top_clipped = self._left_rows == self._detail_rows and self._left_rows > 5
        length = min(5, self._left_rows)
        futures = {}
        for i in range(length):
            row_index = length - 1 - i
            display_row = self._left_rows - i
            future = self._detail_executor.submit(
                _recognize_detail_row_async,
                current_frame,
                self._detail_tag,
                top_clipped,
                row_index,
            )
            futures[future] = display_row

        for future in as_completed(futures):
            display_row = futures[future]
            text, percent = future.result()
            print(f'识别到第{display_row}行数据:{text} {percent}')
            self._detail_tmp_dict[display_row] = text, percent

        self._left_rows -= length
        up_times = 5 if self._left_rows >= 5 else self._left_rows
        if up_times > 0:
            self.macro_text_run("LStick@0,-127:0.15\n0.4", loop=up_times, block=True)
            time.sleep(0.4)
            self._jump_next_frame = True
        else:
            self._cycle_step_index += 1
            return

    def step_1_3(self):
        for k, v in sorted(self._detail_tmp_dict.items()):
            text, percent = v
            if self._detail_tag == DetailTagEnum.Teammate:
                self._pokemon.append_row(self._detail_tag, (text, k))
            else:
                self._pokemon.append_row(self._detail_tag, (text, percent))
        if self._detail_tag == DetailTagEnum.Ability:
            self._cycle_step_index += 1
        else:
            self._detail_index += 1
            self.macro_text_run("R:0.1\n1\nLStick@0,-127:0.15\n0.4\nLStick@0,-127:0.15\n0.4\nLStick@0,-127:0.15\n0.4\nLStick@0,-127:0.15\n0.8", loop=1, block=True)
            self._detail_tag = DetailTagEnum(self._detail_tag.value + 1)
            self._jump_next_frame = True
            self._cycle_step_index -= 2

    def step_2(self):
        print(str(self._pokemon))

        with self._output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(self._pokemon.to_dict(), ensure_ascii=False) + "\n")

        if self._last_pokemon_flg:
            self._finished_process()
            return

        self.macro_text_run("B:0.1\n2\nLStick@0,127:0.1\n0.3", loop=1, block=True)
        self._currentPokemonRank += 1
        self._jump_next_frame = True
        self._cycle_step_index += 1
