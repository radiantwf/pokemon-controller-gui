import json
from . import macro
from macro.run import _run_macro

def published():
    m = macro.Macro()
    if m._publish != None:
        return json.dumps(m._publish, separators=(',', ':'), ensure_ascii=False)
    else:
        return "{}"


def run(macro: str, loop: int = 1, paras: dict = dict(), port: int = 50000):
    _run_macro(macro, loop, paras, port)
