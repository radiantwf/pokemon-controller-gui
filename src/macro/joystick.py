
import multiprocessing
from const import ConstClass
from datatype.input import ControllerInput


class JoyStick(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(JoyStick, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self, controller_input_action_queue: multiprocessing.Queue):
        if JoyStick._first:
            JoyStick._first = False
            self._my_const = ConstClass()
            self._controller_input_action_queue = controller_input_action_queue

    def send_action(self, action: str = ""):
        self._controller_input_action_queue.put(ControllerInput(action))
