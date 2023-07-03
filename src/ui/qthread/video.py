
from PySide6.QtCore import QThread,Signal
from PySide6.QtGui import QImage


class VideoThread(QThread):
    on_recv_frame = Signal(QImage)
    def __init__(self, parent=None,queue=None):
        QThread.__init__(self, parent)
        self._queue = queue
        self._stop_signal = False
        
    def run(self):
        while True:       
            if self._stop_signal:
                break
            frame = None
            while True:
                try:
                    frame = self._queue.get_nowait()
                except:
                    break
            if frame == None:
                continue
            img = QImage(frame.bytes(), frame.width, frame.height, frame.channels*frame.width,QImage.Format_BGR888)
            self.on_recv_frame.emit(img)

    def stop(self):
        self._stop_signal = True

    def __del__(self):
        try:
            self.stop()
            self.wait()
        except:
            pass