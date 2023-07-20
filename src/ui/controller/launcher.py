
import json
import multiprocessing
import sys
import time

from controller.device import SerialDevice

sys.path.append('./src')
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
    
    def list_controller(self):
        return SerialDevice.list_device()
    
    def controller_start(self, device: SerialDevice)->multiprocessing.Queue():
        self.controller_stop()
        self._controller_input_action_queue = multiprocessing.Queue()
        self._controller_process = multiprocessing.Process(
            target=controller.run, args=(device, self._controller_input_action_queue, ))
        self._controller_process.start()
        return self._controller_input_action_queue

    
    def controller_stop(self):
        if self._controller_input_action_queue:
            self._controller_input_action_queue.close()
            self._controller_input_action_queue = None

        if self._controller_process:
            try:
                self._controller_process.terminate()
                self._controller_process.join(1)
                self._controller_process = None
            except:
                self._controller_process.kill()
                self._controller_process = None
    
    def controller_running(self):
        if self._controller_process:
            return self._controller_process.is_alive()
        return False
