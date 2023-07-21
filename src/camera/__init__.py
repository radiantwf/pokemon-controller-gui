import multiprocessing
import signal
from camera.device import CameraDevice
from datatype.frame import Frame
from PySide6.QtMultimedia import QMediaDevices
import cv2
import time
import platform

system = platform.system()


def run(camera_device: CameraDevice, frame_queue: multiprocessing.Queue):
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
    
    # 定义信号处理函数
    def signal_handler(signum, frame):
        cap.release()
        exit(0)
        
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    if frame_queue.full():
                        time.sleep(0.001)
                        continue
                    send_frame = Frame(
                        camera_device.width, camera_device.height, 3, cv2.CAP_PVAPI_PIXELFORMAT_BGR24, frame.tobytes())
                    try:
                        if frame_queue.empty():
                            frame_queue.put_nowait(send_frame)
                    except KeyboardInterrupt:
                        # 处理键盘中断信号
                        signal_handler(signal.SIGINT, None)
                    except:
                        pass
            else:
                break
        except KeyboardInterrupt:
            # 处理键盘中断信号
            signal_handler(signal.SIGINT, None)

    cap.release()