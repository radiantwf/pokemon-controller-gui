import math
import queue
import threading
import cv2
import time

import numpy
from const import ConstClass
from datatype.frame import Frame


def run(stop_event: threading.Event, input_frame_queue: queue.Queue, output_frames_queue: queue.Queue):
    # 上一帧获取时间
    _last_set_frame_time_monotonic = 0
    _my_const = ConstClass()
    _width = _my_const.RecognizeVideoWidth
    _height = _my_const.RecognizeVideoHeight
    _fps = _my_const.RecognizeVideoFps

    while not input_frame_queue.empty():
        input_frame_queue.get_nowait()

    try:
        while True:
            if stop_event.is_set():
                raise InterruptedError
            frame = None
            while not input_frame_queue.empty():
                frame = input_frame_queue.get()
                if stop_event.is_set():
                    raise InterruptedError
            delay = 1.0/_fps - \
                (time.monotonic() - _last_set_frame_time_monotonic)
            if frame is None or delay > 0:
                if frame is None or delay > 0.001:
                    delay = 0.001
                time.sleep(delay)
                continue
            _last_set_frame_time_monotonic = time.monotonic()
            np_array = numpy.frombuffer(
                frame.bytes(), dtype=numpy.uint8)
            mat = np_array.reshape(
                (frame.height, frame.width, frame.channels))
            frame_mat = cv2.resize(
                mat, (_width, _height))
            if not output_frames_queue.full():
                output_frame_mat_1 = frame_mat.copy()
                output_frame_mat_2 = output_frame_mat_1.copy()
                output_frame_mat_3 = output_frame_mat_2.copy()
                output_frames = (Frame(
                    _width, _height, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, output_frame_mat_1.tobytes()), Frame(
                    _width, _height, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, output_frame_mat_2.tobytes()), Frame(
                    _width, _height, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, output_frame_mat_3.tobytes()))
                output_frames_queue.put_nowait(output_frames)
    except InterruptedError:
        return
