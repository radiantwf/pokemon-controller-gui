
import json
import multiprocessing
import sys

sys.path.append('./src')
import recognition

class RecognitionLauncher(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(RecognitionLauncher, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if RecognitionLauncher._first:
            RecognitionLauncher._first = False
            self._recognition_process = None
            self._stop_event = None

    def list_recognition(self):
        scripts = recognition.list_recognition_script()
        return scripts
    
    def recognition_start(self, script_name: str, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        self.recognition_stop()
        self._stop_event = multiprocessing.Event()
        self._recognition_process = multiprocessing.Process(
            target=recognition.run, args=(script_name, self._stop_event, frame_queue, controller_input_action_queue, ))
        self._recognition_process.start()

    
    def recognition_stop(self,timeout = 10):
        if self._recognition_process != None:
            try:
                self._stop_event.set()
                self._recognition_process.join(timeout)
                if self._recognition_process.is_alive():
                    self._recognition_process.terminate()
                else:
                    self._recognition_process = None
                    return True
            except:
                self._recognition_process.terminate()
            self._recognition_process = None
            return False
        return True
    
    def recognition_running(self):
        if self._recognition_process != None:
            return self._recognition_process.is_alive()
        return False
