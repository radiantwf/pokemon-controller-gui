
import queue
import threading
import thread.capture as capture


class CameraLauncher(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CameraLauncher, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if CameraLauncher._first:
            self._camera_list = dict()
            CameraLauncher._first = False
            self._camera_process = None
            self._stop_event = None

    def camera_start(self, camera_frame_queue, recognition_frame_queue) -> queue.Queue():
        self.camera_stop()

        self._stop_event = threading.Event()
        self._camera_process = threading.Thread(
            target=capture.run, args=(self._stop_event, camera_frame_queue, recognition_frame_queue, ))
        self._camera_process.start()
        return

    def camera_stop(self, timeout=1):
        if self._camera_process != None:
            try:
                self._stop_event.set()
                self._camera_process.join(timeout)
                if self._camera_process.is_alive():
                    self._camera_process.terminate()
                else:
                    self._camera_process = None
                    return True
            except:
                self._camera_process.terminate()
            self._camera_process = None
            return False
        return True

    def camera_running(self):
        if self._camera_process:
            return self._camera_process.is_alive()
        return False
