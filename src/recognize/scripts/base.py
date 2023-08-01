import asyncio
import multiprocessing
import time
from log import send_log

from enum import Enum


class WorkflowEnum(Enum):
    Begin = 0
    Preparation = 1
    Circle = 2
    End = 3


class Base(object):
    def __init__(self, frame_queue: multiprocessing.Queue):
        # 帧队列
        self._frame_queue = frame_queue
        # 当前帧
        self._current_frame = None
        # 运行状态
        self._running_status = None
        # 运行开始时间
        self._run_start_time_monotonic = 0
        # 准备期帧数
        self._preparation_frame_count = -1
        # 首次循环周期开始时间
        self._first_circle_begin_time_monotonic = 0
        # 循环周期开始时间
        self._current_circle_begin_time_monotonic = 0
        # 循环周期内帧数
        self._current_circle_frame_count = -1
        # 循环重新开始标志
        self._circle_continue_flag = False

    async def process_frame(self):
        pass

    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def on_error(self):
        pass

    # 当前帧
    @property
    def current_frame(self):
        return self._current_frame

    def send_log(self, msg):
        send_log(msg)

    def set_circle_begin(self):
        if self._first_circle_begin_time_monotonic == 0:
            self._first_circle_begin_time_monotonic = time.monotonic()

    def set_circle_continue(self):
        pass

    def set_circle_end(self):
        pass

    async def run(self):
        self._run_start_time_monotonic = time.monotonic()
        self._running_status = WorkflowEnum.Begin
        await self.on_start()
        try:
            while not self._frame_queue.close():
                frame = None
                while self._frame_queue.empty():
                    frame = self._frame_queue.get()
                if frame is None:
                    await asyncio.sleep(0.001)
                    continue

                # 设置准备状态
                if self._running_status == WorkflowEnum.Begin:
                    self._running_status = WorkflowEnum.Preparation
                    self._preparation_frame_count = 0
                elif self._running_status == WorkflowEnum.Preparation:
                    self._preparation_frame_count += 1
                elif self._running_status == WorkflowEnum.Circle:
                    self._circle_frame_count += 1

                self._current_frame = frame
                self.process_frame()

                # 设置循环状态
                if self._running_status == WorkflowEnum.Preparation and self._first_circle_begin_time_monotonic > 0:
                    self._running_status = WorkflowEnum.Circle
                    self._on_circle()
                    self._first_circle_begin_time_monotonic = self._circle_begin_time_monotonic

                if self._circle_continue_flag:
                    self._circle_frame_count += 1
                    self._circle_continue_flag = False
                    self._circle_begin()
                else:
                    self._circle_frame_count += 1
        except InterruptedError:
            await self.on_stop()
        except Exception as e:
            await self.on_error()
            raise e
        finally:
            await self.on_stop()

    def _on_circle(self):
        self._circle_begin_time_monotonic = time.monotonic()
        self._circle_frame_count = 0
