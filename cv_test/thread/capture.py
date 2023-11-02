import math
import queue
import threading
from PySide6.QtMultimedia import QMediaDevices
import cv2
import time
import platform
from datatype.frame import Frame

system = platform.system()


def run(stop_event: threading.Event, frame_queue: queue.Queue, recognition_frame_queue: queue.Queue):
    _camera(stop_event, frame_queue, recognition_frame_queue)
    # _video(stop_event, frame_queue, recognition_frame_queue)


def _video(stop_event: threading.Event, frame_queue: queue.Queue, recognition_frame_queue: queue.Queue, strat_ts: float = 0.0):
    cap = cv2.VideoCapture('yolo_training/data/2023-10-29 01-28-46.mp4')
    # 获取视频的帧率
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    video_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    # 获取视频的总帧数
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    init_frame = math.ceil(fps * strat_ts)
    init_time = time.monotonic()
    last_frame = -1

    while True:
        try:
            if stop_event.is_set():
                raise InterruptedError
            time.sleep(0.001)
            current_frame = int(
                init_frame + (time.monotonic() - init_time) * fps)
            if current_frame >= total_frames:
                break
            if current_frame <= last_frame:
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            last_frame = current_frame
            ret, frame = cap.read()
            if ret:
                send_frame = Frame(
                    video_width, video_height, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, frame.tobytes())
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


def _camera(stop_event: threading.Event, frame_queue: queue.Queue, recognition_frame_queue: queue.Queue):
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
