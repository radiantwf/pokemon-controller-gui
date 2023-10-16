
from abc import ABC, abstractmethod
from enum import Enum
import time
from typing import final
from recognition.scripts.base.base_script import BaseScript


class SubStepRunningStatus(Enum):
    NotStarted = -1
    Running = 0
    OK = 1
    Finished = 2
    Failed = 3
    Exception = 4
    Timeout = 5
    Interrupted = 6


class BaseSubStep(ABC):
    def __init__(self, script: BaseScript, timeout: float = 0.0) -> None:
        if not isinstance(script, BaseScript):
            raise TypeError("script must be an instance of BaseScript")
        if not script:
            raise ValueError("script must be initialized")
        self._script = script
        self._timeout = timeout
        self._running_status = SubStepRunningStatus.NotStarted
        self._begin_time_monotonic = 0
        self._begin_frame_count = 0
        self._finish_time_monotonic = 0
        self._jump_next_frame = False

    @final
    @property
    def script(self) -> BaseScript:
        return self._script

    @final
    @property
    def running_status(self) -> SubStepRunningStatus:
        return self._running_status

    # @final
    # @running_status.setter
    # def running_status(self, value):
    #     self._running_status = value

    @final
    def jump_next_frame(self):
        self._jump_next_frame = True

    @final
    def time_sleep(self, seconds: float):
        time.sleep(seconds)
        self.jump_next_frame()

    @final
    def run(self) -> SubStepRunningStatus:
        if self._running_status == SubStepRunningStatus.NotStarted:
            self._begin_time_monotonic = time.monotonic()
            self._begin_frame_count = self._script.current_frame_count
            self._running_status = SubStepRunningStatus.Running
            return self._running_status
        elif self._running_status != SubStepRunningStatus.Running:
            return self._running_status
        if self._timeout > 0.0 and time.monotonic() - self._begin_time_monotonic > self._timeout:
            self._running_status = SubStepRunningStatus.Timeout
            return self._running_status
        try:
            if self._jump_next_frame:
                self._jump_next_frame = False
                return self._running_status
            self._running_status = self._process()
            return self._running_status
        except Exception as e:
            self._running_status = SubStepRunningStatus.Exception
            raise e

    @abstractmethod
    def _process(self) -> SubStepRunningStatus:
        pass
