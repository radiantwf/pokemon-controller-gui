import multiprocessing
from camera.device import CameraDevice
from datatype.frame import Frame
from PySide6.QtMultimedia import QMediaDevices
import cv2
import time
import platform

system = platform.system()


def run(camera_device: CameraDevice, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, recognition_frame_queue: multiprocessing.Queue):
    id = -1
    cameras = QMediaDevices.videoInputs()
    cameras.sort(key=lambda x: x.id().data())
    for i, camera_info in enumerate(cameras):
        if camera_info.id().data().decode() == camera_device.id:
            id = i
            break
    if id < 0:
        return
    if system == 'Windows':
        cap = cv2.VideoCapture(id, cv2.CAP_DSHOW)
    elif system == 'Darwin':
        cap = cv2.VideoCapture(id)
    else:
        cap = cv2.VideoCapture(id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_device.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_device.height)
    cap.set(cv2.CAP_PROP_POS_FRAMES, camera_device.fps)

    while True:
        try:
            if stop_event.is_set():
                raise InterruptedError
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    send_frame = Frame(
                        camera_device.width, camera_device.height, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, frame.tobytes())
                    if frame_queue.empty():
                        frame_queue.put(send_frame)
                    if recognition_frame_queue.empty():
                        recognition_frame_queue.put(send_frame)
            else:
                break
        except InterruptedError:
            cap.release()
            exit(0)

    cap.release()