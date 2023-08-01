import multiprocessing
from controller.action_display import send_action_display

from controller.device import SerialDevice
from controller.switch_pro import SwitchProController


def run(device: SerialDevice, stop_event: multiprocessing.Event, controller_input_action_queue: multiprocessing.Queue):
    controller = SwitchProController()
    if not controller.open(device):
        exit(-1)

    try:
        # 循环读取队列内容
        action = None
        while True:
            if stop_event.is_set():
                raise InterruptedError
            while not controller_input_action_queue.empty():
                action = controller_input_action_queue.get()
            if action:
                controller.send_action(action)
                send_action_display(action)
                action = None
            else:
                action = controller_input_action_queue.get()
    except InterruptedError:
        controller.close()
        exit(0)