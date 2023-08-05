
import multiprocessing
from camera.device import CameraDevice
import camera

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
    
    def list_camera(self):
        return CameraDevice.list_device()
    
    def camera_start(self, device: CameraDevice, camera_frame_queue, recognition_frame_queue)->multiprocessing.Queue():
        self.camera_stop()

        self._stop_event = multiprocessing.Event()
        self._camera_process = multiprocessing.Process(
            target=camera.run, args=(device, self._stop_event, camera_frame_queue, recognition_frame_queue, ))
        self._camera_process.start()
        return

    
    def camera_stop(self,timeout = 1):
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
