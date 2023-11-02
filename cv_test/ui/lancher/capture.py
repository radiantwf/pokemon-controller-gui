
import queue
import threading
import thread.capture as capture


class CaptureLauncher(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CaptureLauncher, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if CaptureLauncher._first:
            CaptureLauncher._first = False
            self._capture_thread = None
            self._stop_event = None

    def capture_start(self, capture_frame_queue, recognition_frame_queue) -> queue.Queue():
        self.capture_stop()

        self._stop_event = threading.Event()
        self._capture_thread = threading.Thread(
            target=capture.run, args=(self._stop_event, capture_frame_queue, recognition_frame_queue, ))
        self._capture_thread.start()
        return

    def capture_stop(self, timeout=1):
        if self._capture_thread != None:
            try:
                self._stop_event.set()
                self._capture_thread.join(timeout)
                if self._capture_thread.is_alive():
                    self._capture_thread.terminate()
                else:
                    self._capture_thread = None
                    return True
            except:
                self._capture_thread.terminate()
            self._capture_thread = None
            return False
        return True

    def capture_running(self):
        if self._capture_thread:
            return self._capture_thread.is_alive()
        return False
