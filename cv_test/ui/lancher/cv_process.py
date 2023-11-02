
import queue
import threading

import thread.cv_process as cv_process


class CVProcessLauncher(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CVProcessLauncher, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if CVProcessLauncher._first:
            CVProcessLauncher._first = False
            self._cv_thread = None
            self._stop_event = None

    def cv_process_start(self, recognition_frame_queue, processed_frames_queue) -> queue.Queue():
        self.cv_process_stop()

        self._stop_event = threading.Event()
        self._cv_thread = threading.Thread(
            target=cv_process.run, args=(self._stop_event, recognition_frame_queue, processed_frames_queue, ))
        self._cv_thread.start()
        return

    def cv_process_stop(self, timeout=1):
        if self._cv_thread != None:
            try:
                self._stop_event.set()
                self._cv_thread.join(timeout)
                if self._cv_thread.is_alive():
                    self._cv_thread.terminate()
                else:
                    self._cv_thread = None
                    return True
            except:
                self._cv_thread.terminate()
            self._cv_thread = None
            return False
        return True

    def cv_process_running(self):
        if self._cv_thread:
            return self._cv_thread.is_alive()
        return False
