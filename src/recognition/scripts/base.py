from abc import ABC, abstractmethod
import asyncio
import multiprocessing
import sys
import time
from typing import final
from log import send_log
from const import ConstClass

from enum import Enum

sys.path.append('./src')
import macro

class WorkflowEnum(Enum):
    Begin = 0
    Preparation = 1
    Circle = 2
    AfterCircle = 3
    End = 4


class BaseScript(ABC):
    def __init__(self, script_name, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        # 停止事件
        self._stop_event = stop_event
        # 帧队列
        self._frame_queue = frame_queue
        # 控制器输入队列
        self._controller_input_action_queue = controller_input_action_queue
        self._script_name = script_name
        self._my_const = ConstClass()
        self._width = self.__my_const.RecognizeVideoWidth
        self._height = self.__my_const.RecognizeVideoHeight
        self._fps = self.__my_const.RecognizeVideoFps
        
        # 宏进程
        self._macro_process = None
        self._macro_stop_event = None
        # 当前帧
        self._current_frame = None
        # 运行状态
        self._running_status = None
        # 运行开始时间
        self._run_start_time_monotonic = 0
        # 准备期帧数
        self._preparation_frame_count = -1
        # 跳出循环后帧数
        self._after_cycle_frame_count = -1
        # 首次循环周期开始时间
        self._first_circle_begin_time_monotonic = 0
        # 当前循环开始时间
        self._current_circle_begin_time_monotonic = 0
        # 当前循环帧数
        self._current_circle_frame_count = -1
        # 循环重新开始标志
        self._circle_continue_flag = False
        # 循环跳出标志
        self._circle_break_flag = False
        # 循环跳出时间
        self._circle_break_time_monotonic = 0
        # 结束标志
        self._stop_flag = True
        # 上一帧获取时间
        self._last_set_frame_time_monotonic = 0

    @abstractmethod
    def process_frame(self):
        pass

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_stop(self):
        pass

    @abstractmethod
    def on_error(self):
        pass

    # 当前帧
    @final
    @property
    def current_frame(self):
        return self._current_frame
    
    # 运行状态
    @final
    @property
    def running_status(self):
        return self._running_status
    
    @final
    @property
    def current_frame_count(self):
        if self._running_status == WorkflowEnum.Preparation:
            return self._preparation_frame_count
        elif self._running_status == WorkflowEnum.Circle:
            return self._current_circle_frame_count
        elif self._running_status == WorkflowEnum.AfterCircle:
            return self._after_cycle_frame_count   
        elif self._running_status == WorkflowEnum.End:
            return 0
    
    # 运行宏命令
    @final
    def macro_run(self, macro_name, loop=1, paras={}, block:bool=True, timeout:float=None):
        self.macro_stop()

        self._macro_stop_event = multiprocessing.Event()
        self._macro_process = multiprocessing.Process(
            target=macro.run, args=(macro_name, self._macro_stop_event, self._controller_input_action_queue, loop, paras, False))
        self._macro_process.start()
        if not block:
            return True
        start_monotonic = time.monotonic()
        while self._macro_process.is_alive():
            time.sleep(0.1)
            if timeout != None and timeout > 0 and time.monotonic() - start_monotonic > timeout:
                return self.macro_stop(timeout=None)
        self._macro_stop_event = None
        return True
    # 停止宏命令
    @final
    def macro_stop(self, block=True, timeout = None):
        if self._macro_process != None:
            if self._macro_process.is_alive():
                if block:
                    try:
                        self._macro_stop_event.set()
                        self._macro_process.join(timeout)
                        if self._macro_process.is_alive():
                            self._macro_process.terminate()
                        else:
                            self._macro_process = None
                            return True
                    except:
                        self._macro_process.terminate()
                    self._macro_process = None
                    return False
                else:
                    self._macro_stop_event.set()
                    return True
            else:
                self._macro_process = None
        return True
    
    # 发送日志
    @final
    def send_log(self, msg):
        send_log(msg)

    # 开始循环
    @final
    def set_circle_begin(self):
        if self._first_circle_begin_time_monotonic == 0:
            self._first_circle_begin_time_monotonic = time.monotonic()

    # 继续循环
    @final
    def set_circle_continue(self):
        self._circle_continue_flag = True

    # 跳出循环
    @final
    def set_circle_end(self):
        self._circle_break_flag = True
    
    # 结束
    @final
    def stop_work(self):
        self._stop_flag = True

    # 运行
    @final
    def run(self):
        self._on_start()
        try:
            while not self._frame_queue.close():
                if self._stop_event.is_set():
                    raise InterruptedError
                if self._stop_flag:
                    return
                frame = None
                while not self._frame_queue.empty():
                    if self._stop_event.is_set():
                        raise InterruptedError
                    if self._stop_flag:
                        return
                    frame = self._frame_queue.get()
                if frame is None or time.monotonic() - self._last_set_frame_time_monotonic < 1.0/self._fps:
                    asyncio.sleep(0.001)
                    continue

                # 设置准备状态
                if self._running_status == WorkflowEnum.Begin:
                    self._running_status = WorkflowEnum.Preparation
                    self._preparation_frame_count = 0
                elif self._running_status == WorkflowEnum.Preparation:
                    self._preparation_frame_count += 1
                elif self._running_status == WorkflowEnum.Circle:
                    self._current_circle_frame_count += 1
                elif self._running_status == WorkflowEnum.Circle:
                    self._current_circle_frame_count += 1
                elif self._running_status == WorkflowEnum.AfterCircle:
                    self._after_cycle_frame_count += 1

                self._last_set_frame_time_monotonic = time.monotonic()
                self._current_frame = frame
                self.process_frame()

                if self._running_status == WorkflowEnum.Preparation and self._first_circle_begin_time_monotonic > 0:
                    self._on_circle()
                    self._first_circle_begin_time_monotonic = self._current_circle_begin_time_monotonic
                elif self._running_status == WorkflowEnum.Circle and self._circle_continue_flag:
                    self._circle_continue_flag = False
                    self._on_circle()
                elif self._running_status == WorkflowEnum.Circle and self._circle_break_flag:
                    self._on_circle_break()
                
                # 抽取一帧后，如果队列中还有帧，则清空队列堆积数据
                if not self._frame_queue.close():
                    while not self._frame_queue.empty():
                        if self._stop_flag:
                            return
                        self._frame_queue.get()
        except InterruptedError:
            return
        except Exception as e:
            self.on_error()
            raise e
        finally:
            self.macro_stop(timeout=1)
            self._on_stop()

    @final
    def _on_circle(self):
        self._running_status = WorkflowEnum.Circle
        self._current_circle_begin_time_monotonic = time.monotonic()
        self._current_circle_frame_count = 0

    @final
    def _on_circle_break(self):
        self._running_status = WorkflowEnum.AfterCircle
        self._circle_break_time_monotonic = time.monotonic()
        self._after_cycle_frame_count = 0

    @final
    def _on_start(self):
        self._run_start_time_monotonic = time.monotonic()
        self._running_status = WorkflowEnum.Begin
        self.on_start()

    @final
    def _on_stop(self):
        self._running_status = WorkflowEnum.End
        self.on_stop()