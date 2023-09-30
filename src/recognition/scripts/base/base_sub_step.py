
from abc import ABC, abstractmethod
from enum import Enum
import time
from typing import final
from recognition.scripts.base.base_script import BaseScript


class SubStepRunningStatus(Enum):
    NotStarted = -1
    Running = 0
    OK = 1
    Failed = 2
    Exception = 3
    Timeout = 4


class BaseSubStep(ABC):
    def __init__(self, script: BaseScript,timeout:float = 0.0) -> None:
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
            self._running_status = self._process()
            return self._running_status
        except Exception as e:
            self._running_status = SubStepRunningStatus.Exception
            raise e

    @abstractmethod
    def _process(self) -> SubStepRunningStatus:
        pass
