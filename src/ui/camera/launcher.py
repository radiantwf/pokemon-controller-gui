
import multiprocessing
import sys

from camera.device import CameraDevice

sys.path.append('./src')
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
            self._camera_frame_queue = None
    
    def list_camera(self):
        return CameraDevice.list_device()
    
    def camera_start(self, device: CameraDevice)->multiprocessing.Queue():
        self.camera_stop()
        self._camera_frame_queue = multiprocessing.Queue(1)

        self._camera_process = multiprocessing.Process(
            target=camera.run, args=(device, self._camera_frame_queue, ))
        self._camera_process.start()
        return self._camera_frame_queue

    
    def camera_stop(self):
        if self._camera_frame_queue:
            self._camera_frame_queue.close()
            self._camera_frame_queue = None
            
        if self._camera_process:
            try:
                self._camera_process.terminate()
                self._camera_process.join(1)
                self._camera_process = None
            except:
                self._camera_process.kill()
                self._camera_process = None
    
    def camera_running(self):
        if self._camera_process:
            return self._camera_process.is_alive()
        return False
