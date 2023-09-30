from enum import Enum
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep


class SVOpenMenuStatus(Enum):
    Processing = 0
    OK = 1


class SVOpenMenu(BaseSubStep):
    def __init__(self, script: BaseScript) -> None:
        super().__init__(script)
        
    def open_menu(self) -> SVOpenMenuStatus:
        # 连续点击B 持续2秒
        self.macro_text_run("B:0.1\n0.1", loop=10, block=True)
        return SVOpenMenuStatus.OK
