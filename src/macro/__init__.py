import json
import multiprocessing
from . import macro
from macro.run import _run_macro, _run_macro_text


def published():
    m = macro.Macro()
    m.reload()
    if m._publish != None:
        return json.dumps(m._publish, separators=(',', ':'), ensure_ascii=False)
    else:
        return "{}"


def run(macro_name: str, stop_event, controller_input_action_queue: multiprocessing.Queue, loop: int = 1, paras: dict = dict(), log=True):
    m = macro.Macro()
    m.reload()
    summary = macro_name
    for iter in m._publish:
        if iter["name"] == macro_name:
            summary = iter["summary"]
            break
    _run_macro(macro_name, stop_event, controller_input_action_queue,
               summary, loop, paras, log)


def run_text(text: str, stop_event, controller_input_action_queue: multiprocessing.Queue, summary: str = "", loop: int = 1, paras: dict = dict(), log=False):
    m = macro.Macro()
    m.reload()
    _run_macro_text(text, stop_event,
                    controller_input_action_queue, summary, loop, paras, log)
