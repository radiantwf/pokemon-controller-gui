import threading
from PySide6.QtMultimedia import QMediaDevices
import cv2
import time
import platform
from src.datatype.frame import Frame

system = platform.system()


def run(stop_event: threading.Event, frame_queue: threading.Queue, recognition_frame_queue: threading.Queue):
    _camera(stop_event,frame_queue,recognition_frame_queue)
    

def _video(stop_event: threading.Event, frame_queue: threading.Queue, recognition_frame_queue: threading.Queue):
    pass

def _camera(stop_event: threading.Event, frame_queue: threading.Queue, recognition_frame_queue: threading.Queue):
    id = 0
    if system == 'Windows':
        cap = cv2.VideoCapture(id, cv2.CAP_DSHOW)
    elif system == 'Darwin':
        cap = cv2.VideoCapture(id)
    else:
        cap = cv2.VideoCapture(id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 60)

    while True:
        try:
            if stop_event.is_set():
                raise InterruptedError
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    send_frame = Frame(
                        1920, 1080, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, frame.tobytes())
                    if not frame_queue.full():
                        frame_queue.put_nowait(send_frame)
                    if not recognition_frame_queue.full():
                        recognition_frame_queue.put_nowait(send_frame)
            else:
                break
        except InterruptedError:
            cap.release()
            exit(0)

    cap.release()