import sys

import numpy

sys.path.append('./src')
# from macro import test
import camera
from datatype.frame import Frame
import ui
import cv2
import multiprocessing
import time
from const import ConstClass
from PySide6.QtGui import QImage

# import controller
# import recognize
def main():
    my_const = ConstClass()
    # print(test())
    main_video_frame,capture_video_frame = multiprocessing.Pipe(False)
    ui_display_video_frame = multiprocessing.Queue()
    opencv_processed_video_frame = multiprocessing.Queue()
    recognize_video_frame = multiprocessing.Queue(1)
    frame_queues = (recognize_video_frame,ui_display_video_frame,opencv_processed_video_frame,)
    camera_control_queue = multiprocessing.Queue()
    ui_process = multiprocessing.Process(target=ui.run, args=(camera_control_queue,frame_queues,))
    ui_process.start()
    video_process = multiprocessing.Process(target=camera.capture_video, args=(camera_control_queue,capture_video_frame,))
    video_process.start()
    try:
        while True:
            if not ui_process.is_alive():
                break
            if main_video_frame.poll():
                video_frame = main_video_frame.recv()
                try:
                    np_array = numpy.frombuffer(video_frame.bytes(), dtype=numpy.uint8)
                    mat = np_array.reshape((video_frame.height, video_frame.width, video_frame.channels))
                    display_mat = cv2.resize(mat, (my_const.DisplayCameraWidth,my_const.DisplayCameraHeight), interpolation=cv2.INTER_AREA)
                    ui_display_video_frame.put(Frame(my_const.DisplayCameraWidth,my_const.DisplayCameraHeight,video_frame.channels,video_frame.format,display_mat),False,0)
                except:
                    pass
            # try:
            #     recognize_video_frame.put(video_frame,False,0)
            # except:
            #     pass
            else:
                time.sleep(0.001)
    except:
        pass
    # recognize_process.kill()
    video_process.kill()
    ui_process.kill()
    sys.exit(0)
    # dev_video = device.VideoDevice(name=_Camera_Name,width=_Camera_Width,height=_Camera_Height,fps=_Camera_FPS,index=0,pix_fmt=None)
    # # dev_video = device.VideoDevice(name=_Camera_Name,width=_Camera_Width,height=_Camera_Height,fps=_Camera_FPS,index=0,pix_fmt=None,vcodec="mjpeg")
    # # dev_video = device.VideoDevice(name=_Camera_Name,width=_Camera_Width,height=_Camera_Height,fps=_Camera_FPS,index=1,pix_fmt="bgr0")
    # dev_audio = device.AudioDevice(name=_Audio_Device_Name,sample_rate=44100,channels=2)
    # dev_joystick = device.JoystickDevice(host="192.168.50.120",port=5000)
    # main_video_frame,capture_video_frame = multiprocessing.Pipe(False)

    # controller_action_queue = multiprocessing.Queue()
    # opencv_processed_control_queue = multiprocessing.Queue()
    # control_queues=(opencv_processed_control_queue,controller_action_queue,)
    # controller_process = multiprocessing.Process(target=controller.run, args=(dev_joystick,control_queues,))
    # controller_process.start()
    # ui_process = multiprocessing.Process(target=ui.run, args=(frame_queues,control_queues,dev_audio,_Display_Width,_Display_Height))
    # ui_process.start()
    # recognize_process = multiprocessing.Process(target=recognize.run, args=(frame_queues,control_queues,_Display_Width,_Display_Height,_Recognize_FPS,))
    # recognize_process.start()
    # video_process = multiprocessing.Process(target=camera.capture_video, args=(capture_video_frame,dev_video,_Display_Width,_Display_Height,_Display_FPS,))
    # video_process.start()
    # try:
    #     while True:
    #         if not ui_process.is_alive():
    #             break
    #         video_frame = main_video_frame.recv()
    #         try:
    #             ui_display_video_frame.put(video_frame,False,0)
    #         except:
    #             pass
    #         try:
    #             recognize_video_frame.put(video_frame,False,0)
    #         except:
    #             pass
    #         time.sleep(0.001)
    #     sys.exit(0)
    # except:
    #     pass
    # finally:
    #     controller_process.kill()
    #     video_process.kill()
    #     recognize_process.kill()
    #     ui_process.kill()

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    main()

