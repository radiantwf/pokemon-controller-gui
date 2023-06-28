
from PySide6.QtCore import QThread,Signal


class ControllerThread(QThread):
    video_frame = Signal(str)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def set_input(self,queue):
        self._queue = queue
        
    def run(self):
        while True:
            action = None
            while True:
                try:
                    action = self._queue.get_nowait()
                except:
                    break
            if action == None:
                continue
            # self.video_frame.emit(action)