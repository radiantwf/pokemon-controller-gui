
import queue
import time
from PySide6.QtCore import QThread, Signal
from datatype.frame import Frame


class ProcessedDisplayThread(QThread):
    display_frames = Signal(list)

    def __init__(self, parent=None, queue: queue.Queue = None):
        QThread.__init__(self, parent)
        self._queue = queue
        self._stop_signal = False

    def run(self):
        while True:
            if self._stop_signal:
                break
            frames = None
            while not self._queue.empty():
                frames = self._queue.get()
                if self._stop_signal:
                    break
            if frames == None:
                time.sleep(0.001)
                continue
            self.display_frames.emit(frames)

    def stop(self):
        self._stop_signal = True

    def __del__(self):
        try:
            self.stop()
            self.wait()
        except:
            pass
