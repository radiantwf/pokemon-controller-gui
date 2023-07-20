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


def run(macro: str, summary: str, controller_input_action_queue: multiprocessing.Queue, loop: int = 1, paras: dict = dict()):
    _run_macro(macro, summary, controller_input_action_queue, loop, paras)
