from capture import video
import datatype.device as device
import multiprocessing

def capture_video(control_queue:multiprocessing.Queue,pipe:multiprocessing.Pipe):
	video.Video().run(control_queue,pipe)
