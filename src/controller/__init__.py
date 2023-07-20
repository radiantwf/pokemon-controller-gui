import multiprocessing
import signal
import time
from controller.action_display import send_action_display

from controller.device import SerialDevice
from controller.switch_pro import SwitchProControll


def run(device: SerialDevice, controller_input_action_queue: multiprocessing.Queue):
    controller = SwitchProControll()
    if not controller.open(device):
        exit(-1)

    # 定义信号处理函数
    def signal_handler(signum, frame):
        controller.close()
        print('Received signal', signum)
        # 清空队列
        while not controller_input_action_queue.empty():
            controller_input_action_queue.get()
        # 退出进程
        exit(0)

    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)

    # 循环读取队列内容
    action = None
    while True:
        try:
            while not controller_input_action_queue.empty():
                action = controller_input_action_queue.get()
            if action:
                controller.send_action(action)
                send_action_display(action)
                action = None
            else:
                action = controller_input_action_queue.get()
        except KeyboardInterrupt:
            # 处理键盘中断信号
            signal_handler(signal.SIGINT, None)