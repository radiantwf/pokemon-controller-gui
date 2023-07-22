
import queue
import time
from PySide6.QtCore import QThread, Signal
from datatype.frame import Frame
import multiprocessing

class VideoThread(QThread):
    on_recv_frame = Signal(Frame)

    def __init__(self, parent=None, queue:multiprocessing.Queue=None):
        QThread.__init__(self, parent)
        self._queue = queue
        self._stop_signal = False

    def run(self):
        while True:
            frame = None
            while True:
                if self._stop_signal:
                    break
                try:
                    frame = self._queue.get_nowait()
                except ValueError:
                    return
                except queue.Empty:
                    break
            if frame == None:
                continue
            self.on_recv_frame.emit(frame)

    def stop(self):
        self._stop_signal = True
        self._queue.close()

    def __del__(self):
        try:
            self.stop()
            self.wait()
        except:
            pass
