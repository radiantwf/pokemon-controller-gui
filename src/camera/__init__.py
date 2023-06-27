from camera import video
import datatype.frame as frame
import multiprocessing

def capture_video(control_queue:multiprocessing.Queue,pipe:multiprocessing.Pipe):
	video.Video().run(control_queue,pipe)
