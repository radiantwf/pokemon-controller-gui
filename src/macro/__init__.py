
import json
from . import macro


def test():
    m= macro.Macro()
    if m._publish!= None:
        return json.dumps(m._publish, separators=(',', ':'), ensure_ascii=False)
    else:
        return ""