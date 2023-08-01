import json
import multiprocessing
from . import macro
from macro.run import _run_macro

def published():
    m = macro.Macro()
    m.reload()
    if m._publish != None:
        return json.dumps(m._publish, separators=(',', ':'), ensure_ascii=False)
    else:
        return "{}"


def run(macro_name: str, stop_event: multiprocessing.Event, controller_input_action_queue: multiprocessing.Queue, loop: int = 1, paras: dict = dict(), log = True):
    m = macro.Macro()
    m.reload()
    summary = macro_name
    for iter in m._publish:
        if iter["name"] == macro_name:
            summary = iter["summary"]
            break
    _run_macro(macro_name, stop_event, controller_input_action_queue, summary, loop, paras, log)
