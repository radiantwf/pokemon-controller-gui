import json
from . import macro


def published():
    m = macro.Macro()
    if m._publish != None:
        return json.dumps(m._publish, separators=(',', ':'), ensure_ascii=False)
    else:
        return "{}"
