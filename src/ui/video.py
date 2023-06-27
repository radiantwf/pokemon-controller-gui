
from PySide6.QtCore import QThread,Signal
from PySide6.QtGui import QImage


class VideoThread(QThread):
    video_frame = Signal(QImage)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def set_input(self,queue):
        self._queue = queue
        
    def run(self):
        while True:
            frame = None
            while True:
                try:
                    frame = self._queue.get_nowait()
                except:
                    break
            if frame == None:
                continue
            img = QImage(frame.bytes(), frame.width, frame.height, frame.channels*frame.width,QImage.Format_BGR888)
            self.video_frame.emit(img)