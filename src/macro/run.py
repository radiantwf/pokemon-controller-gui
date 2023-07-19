import time
from log import send_log

from macro.joystick import JoyStick
from . import action

_Min_Key_Send_Span = 0.001


def _run_macro(name: str, summary: str, loop: int = 1, paras: dict = dict(), port: int = 50000):
    joystick = JoyStick(port)
    # msg = "开始运行{}脚本，循环次数：{}".format(name, loop)
    times = 0
    if loop <= 0:
        loop = -1
    global _current_info
    global _result_info
    global _start_time
    start_ts = time.monotonic()
    _start_time = start_ts
    try:
        act = _get_action(name, paras)
        if act == None:
            _result_info = "不存在名称为{}的脚本".format(name)
            send_log(_result_info)
            return
        _result_info = ""
        _current_info = "正在运行 [{}] 脚本，已运行{}次，计划运行{}次\n".format(
            summary, times, loop)
        send_log(_current_info)
        last_send_log_ts = time.monotonic()
        while True:
            while True:
                ret = act.pop()
                # print(ret[0])
                if ret[0] != None:
                    _run_line(joystick, ret[0])
                if ret[1]:
                    break
            times += 1
            if time.monotonic() - last_send_log_ts >= 5:
                _current_info = "正在运行 [{}] 脚本，已运行{}次，计划运行{}次\n".format(
                    summary, times, loop)
                send_log(_current_info)
                last_send_log_ts = time.monotonic()
            if loop > 0 and times >= loop:
                break
            act.cycle_reset()
        # msg = "脚本{}运行完成，当前运行次数：{}".format(name, times)
        span = int(time.monotonic() - start_ts)
        _result_info = "[{}] 脚本运行完成，实际运行{}次\n持续运行时间：{:.0f}小时{:.0f}分{:.0f}秒".format(
            summary, times, span/3600, (span % 3600)/60, span % 60)
        send_log(_result_info)
    except InterruptedError:
        # msg = "脚本{}运行中止，当前运行次数：{}".format(name, times)
        span = int(time.monotonic() - start_ts)
        _result_info = "[{}] 脚本停止，实际运行{}次，计划运行{}次\n持续运行时间：{:.0f}小时{:.0f}分{:.0f}秒".format(
            summary, times, loop, span/3600, (span % 3600)/60, span % 60)
        send_log(_result_info)
    finally:
        _start_time = None
        _current_info = ""


def _get_action(name: str, paras: dict = dict()) -> action.Action:
    act = action.Action(name, paras)
    if act._head == None:
        return None
    return act


def _run_line(joystick: JoyStick, action_line: str):
    inputs = []
    actions = action_line.split("->")
    for action in actions:
        splits = action.split(":")
        if len(splits) > 2:
            continue
        p1 = splits[0]
        p2 = 0.1
        if len(splits) == 1:
            try:
                p2 = float(splits[0])
                p1 = ""
            except:
                pass
        else:
            try:
                p2 = float(splits[1])
            except:
                pass
        inputs.append((p1, p2))
    _key_press(joystick, inputs)


def _key_press(joystick: JoyStick, inputs=[]):
    last_action = ""
    for input_line in inputs:
        last_action = input_line[0]
        if input_line[0] == "~":
            continue
        _send(joystick, input_line[0], input_line[1])
    if last_action != "~":
        release(joystick)


def release(joystick: JoyStick):
    _send(joystick)


def _send(joystick: JoyStick, input_line: str = "", delay: float = 0):
    # print("{}\t{}".format(time.monotonic() - _start_time, input_line))
    first = True
    while True:
        if first:
            first = False
            joystick.send_action(input_line)
            send_time = time.monotonic()
            resend_time = send_time
            time.sleep(_Min_Key_Send_Span)
        if time.monotonic() - send_time >= delay:
            return
        if time.monotonic() - resend_time > 0.005:
            joystick.send_action(input_line)
            resend_time = time.monotonic()
        time.sleep(0.001)
        
