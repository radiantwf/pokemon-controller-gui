import time
import asyncio
from . import action

_last_key_press_ns = time.monotonic_ns()
_Min_Key_Send_Span_ns = 1000000

async def _run_macro(name: str, loop: int = 1, paras: dict = dict()):
    msg = "开始运行{}脚本，循环次数：{}".format(name, loop)
    print(msg)
    times = 0
    if loop <= 0:
        loop = -1
    global _macro_running
    global _current_info
    global _result_info
    global _start_time
    start_ts = time.time()
    _start_time = start_ts
    try:
        act = _get_action(name,paras)
        if act == None:
            _result_info = "不存在名称为{}的脚本".format(name)
            return
        _macro_running = True
        _result_info = ""
        _current_info = "正在运行[{}]脚本，已运行{}次，计划运行{}次\n".format(
            name, times, loop)
        while True:
            while True:
                if not _macro_running:
                    raise asyncio.CancelledError
                ret = act.pop()
                # print(ret[0])
                if ret[0] != None:
                    await joystick.do_action(ret[0])
                if ret[1]:
                    break
            times += 1
            _current_info = "正在运行[{}]脚本，已运行{}次，计划运行{}次\n".format(
                name, times, loop)
            if loop > 0 and times >= loop:
                break
            act.cycle_reset()
        msg = "脚本{}运行完成，当前运行次数：{}".format(name, times)
        print(msg)
        span = time.time() - start_ts
        _result_info = "脚本[{}]运行完成，实际运行{}次\n持续运行时间：{:.0f}小时{:.0f}分{:.0f}秒".format(
            name, times, span/3600, (span % 3600)/60, span % 60)
    except asyncio.CancelledError:
        await joystick.release()
        msg = "脚本{}运行中止，当前运行次数：{}".format(name, times)
        print(msg)
        span = time.time() - start_ts
        _result_info = "脚本[{}]停止，实际运行{}次，计划运行{}次\n持续运行时间：{:.0f}小时{:.0f}分{:.0f}秒".format(
            name, times, loop, span/3600, (span % 3600)/60, span % 60)
    finally:
        _start_time = None
        _macro_running = False
        _current_info = ""

def _get_action(name: str,paras:dict=dict()) -> action.Action:
    act = action.Action(name,paras)
    if act._head == None:
        return None
    return act

async def _run_line(action_line:str):
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
            inputs.append((p1,p2))
        await _key_press(inputs)

async def _key_press(inputs = []):
    release_monotonic_ns = 0
    last_action = ""
    for input_line in inputs:
        last_action = input_line
        if input_line == "~":
            continue
        await _send(input_line[0],release_monotonic_ns)
        release_monotonic_ns = _last_key_press_ns + input_line[1]*1000000000
    if last_action != "~":
        await release(release_monotonic_ns)

async def release(release_monotonic_ns:float = 0):
    await _send("",release_monotonic_ns)


async def _send(input_line: str = "",earliest_send_key_monotonic_ns=0):
    earliest = _last_key_press_ns + _Min_Key_Send_Span_ns
    if earliest < earliest_send_key_monotonic_ns:
        earliest = earliest_send_key_monotonic_ns
    loop = 0
    while True:
        loop += 1
        now = time.monotonic_ns()
        if now >= earliest:
            break
        elif now < earliest - _Min_Key_Send_Span_ns:
            ms = int((earliest - now  - _Min_Key_Send_Span_ns)/1000000)
            await asyncio.sleep_ms(ms)
        else:
            time.sleep(0.0001)
    t1 = time.monotonic_ns()
    await send_realtime_action(input_line)
    _last_key_press_ns = time.monotonic_ns()
    t2 = time.monotonic_ns()