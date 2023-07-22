
import queue
import time
from PySide6.QtCore import QThread, Signal
from datatype.frame import Frame

class DisplayThread(QThread):
    display_frame = Signal(Frame)

    def __init__(self, parent=None, queue:queue.Queue=None):
        QThread.__init__(self, parent)
        self._queue = queue
        self._stop_signal = False

    def run(self):
        while True:
            if self._stop_signal:
                break
            frame = None
            try:
                frame = self._queue.get(True,0.5)
            except queue.Empty:
                continue
            if frame == None:
                time.sleep(0.01)
                continue
            self.display_frame.emit(frame)

    def stop(self):
        self._stop_signal = True

    def __del__(self):
        try:
            self.stop()
            self.wait()
        except:
            pass
