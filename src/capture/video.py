import multiprocessing
from datatype.frame import Frame
import cv2
import time
import platform
from PySide6.QtMultimedia import QMediaDevices

system = platform.system()
class Video():
    def __init__(self):
        self._cap = None
        pass
        
    def run(self,control_queue:multiprocessing.Queue,pipe:multiprocessing.Pipe):
        while True:
            try:
                dev = control_queue.get_nowait()
            except:
                if self._cap == None:
                    time.sleep(0.01)
                    continue
                if self._cap.isOpened():
                    ret, frame = self._cap.read()
                    if ret:
                        if pipe.writable:
                            send_frame = Frame(dev.width,dev.height,3,cv2.CAP_PVAPI_PIXELFORMAT_BGR24,frame.tobytes())
                            pipe.send(send_frame)
                continue
            if dev == None:
                if self._cap != None:
                    self._cap.release()
                    self._cap = None
                continue
            else:
                id = -1
                cameras = QMediaDevices.videoInputs()
                for i,camera_info in enumerate(cameras):
                    if camera_info.id().data().decode() == dev.id:
                        id = i
                        break
                if id < 0:
                    break
                if system == 'Windows':
                    self._cap = cv2.VideoCapture(id,cv2.CAP_DSHOW)
                elif system == 'Darwin':
                    self._cap = cv2.VideoCapture(id)
                else:
                    self._cap = cv2.VideoCapture(id)
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,dev.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT,dev.height)
                self._cap.set(cv2.CAP_PROP_POS_FRAMES,dev.fps)
                # self._cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))

    # def capture(self,pipe,dev:device.VideoDevice,display_width,display_height,display_fps:int):
    #     cap = cv2.VideoCapture(dev.index,cv2.CAP_DSHOW)
    #     cap.set(cv2.CAP_PROP_FRAME_WIDTH,dev.width)
    #     cap.set(cv2.CAP_PROP_FRAME_HEIGHT,dev.height)
    #     cap.set(cv2.CAP_PROP_POS_FRAMES,dev.fps)
    #     cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
    #     if display_fps <= 0:
    #         display_fps = dev.fps
    #     last_cap_monotonic = time.monotonic()
    #     min_interval = 1 / display_fps
    #     while cap.isOpened():
    #         ret, frame = cap.read()
    #         now = time.monotonic()
    #         if now - last_cap_monotonic >= min_interval:
    #             last_cap_monotonic = now
    #             frame = cv2.resize(frame, (display_width, display_height))
    #             if pipe.writable:
    #                 pipe.send(frame.tobytes())
    #     cap.release()
    #     cv2.destroyAllWindows()