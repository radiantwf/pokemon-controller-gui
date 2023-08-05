
import multiprocessing
from controller.device import SerialDevice

import controller

class ControllerLauncher(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(ControllerLauncher, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if ControllerLauncher._first:
            self._controller_list = dict()
            ControllerLauncher._first = False
            self._controller_process = None
            self._controller_input_action_queue = None
            self._stop_event = None
    
    def list_controller(self):
        return SerialDevice.list_device()
    
    def controller_start(self, device: SerialDevice)->multiprocessing.Queue():
        self.controller_stop()
        self._stop_event = multiprocessing.Event()
        self._controller_input_action_queue = multiprocessing.Queue()
        self._controller_process = multiprocessing.Process(
            target=controller.run, args=(device, self._stop_event, self._controller_input_action_queue, ))
        self._controller_process.start()
        return self._controller_input_action_queue

    
    def controller_stop(self, timeout=1):
        if self._controller_input_action_queue:
            self._controller_input_action_queue.close()
            self._controller_input_action_queue = None
        
        if self._controller_process != None:
            try:
                self._stop_event.set()
                self._controller_process.join(timeout)
                if self._controller_process.is_alive():
                    self._controller_process.terminate()
                else:
                    self._controller_process = None
                    return True
            except:
                self._controller_process.terminate()
            self._controller_process = None
            return False
        return True
    
    def controller_running(self):
        if self._controller_process:
            return self._controller_process.is_alive()
        return False
