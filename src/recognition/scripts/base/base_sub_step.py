
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
    Exception = 2

class BaseSubStep(ABC):
    def __init__(self, script: BaseScript) -> None:
        if not isinstance(script, BaseScript):
            raise TypeError("script must be an instance of BaseScript")
        if not script:
            raise ValueError("script must be initialized")
        self._script = script
        self._running_status = SubStepRunningStatus.NotStarted
        self._begin_time_monotonic = 0
        self._begin_frame_count = 0
        self._finish_time_monotonic = 0

    @final
    @property
    def script(self) -> BaseScript:
        return self._script

    @final
    def run(self) -> SubStepRunningStatus:
        if self._running_status == SubStepRunningStatus.NotStarted:
            self._begin_time_monotonic = time.monotonic()
            self._begin_frame_count = self._script.current_frame_count
            self._running_status = SubStepRunningStatus.Running
        elif self._running_status != SubStepRunningStatus.Running:
            return self._running_status
        try:
            return self._process()
        except Exception as e:
            self._running_status = SubStepRunningStatus.Exception
            raise e
        
        
    @abstractmethod
    def _process(self) -> SubStepRunningStatus:
        pass