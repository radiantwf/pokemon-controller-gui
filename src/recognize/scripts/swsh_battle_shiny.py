import multiprocessing
from recognize.scripts.base import BaseScript, WorkflowEnum


class SwshBattleShiny(BaseScript):
    def __init__(self, frame_queue: multiprocessing.Queue):
        super().__init__("剑盾定点刷闪" ,frame_queue)
    

    def process_frame(self):
        if self.running_status ==  WorkflowEnum.Preparation:
            self.set_circle_begin()
            return
        if self.running_status == WorkflowEnum.Circle:
            pass
        if self.running_status == WorkflowEnum.AfterCircle:
            return

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_error(self):
        pass