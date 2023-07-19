import json
from . import macro
from macro.run import _run_macro

def published():
    m = macro.Macro()
    m.reload()
    if m._publish != None:
        return json.dumps(m._publish, separators=(',', ':'), ensure_ascii=False)
    else:
        return "{}"


def run(macro: str, summary: str, loop: int = 1, paras: dict = dict(), port: int = 50000):
    _run_macro(macro, summary, loop, paras, port)
