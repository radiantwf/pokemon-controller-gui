import time

_qwer_keyboards = [['1','2','3','4','5','6','7','8','9','0','@'] \
    ,['Q','W','E','R','T','Y','U','I','O','P','='] \
    ,['A','S','D','F','G','H','J','K','L','&',';'] \
    ,['Z','X','C','V','B','N','M','*','#','!','?']]

def input_text_by_qwer(text: str):
    text = text.upper()
    keyboard_pos = dict()
    for y, row in enumerate(_qwer_keyboards):
        for x, char in enumerate(row):
            keyboard_pos[char] = (x, y)

    current_x, current_y = keyboard_pos['1']
    moves = []

    for char in text:
        if char not in keyboard_pos:
            return []

        target_x, target_y = keyboard_pos[char]
        moves.append((target_x - current_x, target_y - current_y))
        current_x, current_y = target_x, target_y

    return moves

def sleep_precise_ms(ms: float):
    target = ms / 1000.0
    start = time.perf_counter()
    # 当剩余时间 > 0.1 秒时，用 sleep 节省 CPU
    while True:
        elapsed = time.perf_counter() - start
        remaining = target - elapsed
        if remaining <= 0:
            break
        if remaining > 0.1:
            # 睡一半剩余时间，避免睡过头太多
            time.sleep(remaining / 2)
        else:
            # 剩余时间 <= 0.1 秒，开始忙等
            while time.perf_counter() - start < target:
                pass
            break

class Paras(object):
    def __init__(self, default_para: dict, para: dict):
        paras = None
        if default_para != None:
            paras = default_para.copy()
        else:
            paras = dict()

        if para != None:
            for key in para.keys():
                v = para[key]
                if v != None and v != "":
                    paras[key] = v
        globals().update(paras)
        pass

    def exec_str(self, key):
        try:
            key = key.replace("|space|", " ", -1)
            exec(key, globals())
        except:
            return

    def get_bool(self, key) -> bool:
        try:
            key = key.replace("|space|", " ", -1)
            v = eval(key, globals())
        except:
            return False
        if v == None:
            return False
        elif (type(v) is bool):
            return v
        elif (type(v) is str) and v.lower() == "true":
            return True
        return False

    def get_int(self, key) -> int:
        try:
            key = key.replace("|space|", " ", -1)
            v = eval(key, globals())
        except:
            return 0

        if v == None:
            return 0
        elif (type(v) is int):
            return v
        elif (type(v) is float):
            return int(v)
        elif (type(v) is str):
            return int(float(v))
        return 0

    def get_float(self, key) -> float:
        try:
            key = key.replace("|space|", " ", -1)
            v = eval(key, globals())
        except:
            return 0

        if v == None:
            return 0
        elif (type(v) is int):
            return float(v)
        elif (type(v) is float):
            return v
        elif (type(v) is str):
            return float(v)
        return 0
