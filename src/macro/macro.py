from . import node
import os
import io
import time
import random
from typing import Literal

random.seed(time.monotonic_ns())
_S_IFDIR: Literal[16384] = 16384
_MACRO_BASE_PATH = "./resources/macros"
_MACRO_EXT = ".m"
_FINISHED_LINE = "0000000"


class Macro(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Macro, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if Macro._first:
            Macro._first = False
            self._publish = []
            self._default_paras = dict()
            self._dic_macros = self._get_macros()

    def reload(self):
        self._publish = []
        self._default_paras = dict()
        self._dic_macros = self._get_macros()

    def get_node(self, name: str) -> tuple[node.Node, dict]:
        try:
            macro_name = name
            for p in self._publish:
                if p.get("summary") == name:
                    macro_name = p.get("name")
            return (self._dic_macros.get(macro_name), self._default_paras.get(macro_name))
        except:
            return None

    def get_temp_script_node(self, text: str) -> tuple[node.Node, dict]:
        dic = self._read_text(text, dict(), "temp_script")
        rows = dic.get("temp_script")
        if rows == None or len(rows) < 1:
            return None
        action = None
        for row in rows:
            if action == None:
                action = node.Node(row)
            else:
                action = action.append(row)
        return (action.head, dict())

    def _get_macros(self) -> dict:
        dic_action_lines = dict()
        macros = self._walk_macro_files()
        for macro in macros:
            dic_action_lines = self._load_file(macro, dic_action_lines)
        dic_macros = dict()
        for key in dic_action_lines.keys():
            rows = dic_action_lines.get(key)
            if rows != None and len(rows) < 1:
                continue
            action = None
            for row in dic_action_lines.get(key):
                if action == None:
                    action = node.Node(row)
                else:
                    action = action.append(row)
            dic_macros[key] = action.head
        return dic_macros

    def _walk_macro_files(self, base=_MACRO_BASE_PATH):
        ret = []
        for p in os.listdir(base):
            path = "{}/{}".format(base, p)
            if p.startswith('.'):
                continue
            elif p.lower().endswith(_MACRO_EXT):
                ret.append(path)
            elif (os.stat(path)[0] & _S_IFDIR):
                ret.extend(self._walk_macro_files(path))
        return ret

    def _load_file(self, filename, dic=dict()) -> dict:
        try:
            f = open(filename, "rt", encoding="utf-8")
        except:
            return dic
        file_tag = filename[len(_MACRO_BASE_PATH) + 1:(
            len(filename) - len(_MACRO_EXT))].replace("/", ".", -1) + "."
        rows = []
        while True:
            row = f.readline()
            if row == "":
                break
            row = row.strip()
            if row == "":
                continue
            elif row.startswith("--") or row.startswith("#"):
                continue
            row = row.replace(" ", "", -1).replace("\t", "", -1)
            if row.startswith("[") and row.count(".") == 0:
                row = "[" + file_tag + row[1:]
            rows.append(row)
        if len(rows) > 0:
            dic = self._read_segments(rows, dic=dic, file_tag=file_tag)
        f.close()
        return dic

    def _read_text(self, text: str, dic=dict(), name="temp_script") -> dict:
        lines = text.splitlines(True)
        rows = []
        for row in lines:
            row = row.strip()
            if row == "":
                continue
            elif row.startswith("--") or row.startswith("#"):
                continue
            row = row.replace(" ", "", -1).replace("\t", "", -1)
            if row.startswith("[") and row.count(".") == 0:
                row = "[" + file_tag + row[1:]
            rows.append(row)
        if len(rows) > 0:
            dic = self._read_segments(rows, dic=dic, file_tag="", name=name)
        return dic

    def _read_segments(self, src_rows, dic=dict(), file_tag: str = "", name: str = "") -> dict:
        rows = []
        sub_rows = []
        sub = False
        sub_floor = 0
        for row in src_rows:
            if row.startswith("<") and row.endswith(">"):
                if len(rows) > 0:
                    if name != "":
                        rows.append(_FINISHED_LINE)
                        dic[name] = rows
                    rows = []
                name = self._process_title(row[1:len(row) - 1], file_tag)
                sub_rows = []
                sub = False
                continue
            elif sub:
                pass
            elif row.startswith("{"):
                sub = True
                row = row[1:]
            if sub:
                str_io = io.StringIO()
                for index in range(0, len(row)):
                    if row[index] == "}" and sub_floor == 0:
                        sub_row = str_io.getvalue()
                        if len(sub_row) > 0:
                            sub_rows.append(sub_row)
                        if len(sub_rows) == 0:
                            sub = False
                            break
                        sub_name = hex(random.randint(1, time.monotonic_ns()))
                        ends = ""
                        if index < len(row) - 1:
                            ends = row[index + 1:]
                        line = "[{}]{}".format(sub_name, ends)
                        rows.append(line)
                        dic = self._read_segments(sub_rows, dic=dic,
                                                  file_tag="", name=sub_name)
                        sub_rows = []
                        sub = False
                        break
                    elif row[index] == "}" and sub_floor > 0:
                        sub_floor -= 1
                    elif row[index] == "{":
                        sub_floor += 1
                    str_io.write(row[index])
                if sub:
                    sub_row = str_io.getvalue()
                    if len(sub_row) > 0:
                        sub_rows.append(sub_row)
                str_io.close()
            else:
                rows.append(row)
        if len(rows) > 0 and name != "":
            rows.append(_FINISHED_LINE)
            dic[name] = rows
        return dic

    def _process_title(self, title_line: str, file_tag: str = "") -> str:
        splits = title_line.split("--")
        t1 = splits[0].split("|")
        name = file_tag + t1[0]
        summary = ""
        loop = -1
        paras = []
        if t1[0] != "":
            if len(t1) >= 3:
                summary = t1[1]
                try:
                    loop = int(float(t1[2]))
                except:
                    pass
            elif len(t1) == 2:
                summary = t1[1]
        if len(splits) > 1:
            dic_paras = dict()
            for para in splits[1:]:
                p2 = ""
                v = ""
                s = para.split("|")
                p1 = s[0]
                if len(s) >= 3:
                    p2 = s[1]
                    v = s[2]
                elif len(s) == 2:
                    p2 = s[1]
                paras.append(dict({"name": p1, "summary": p2, "default": v}))
                dic_paras[p1] = v
            self._default_paras[name] = dic_paras

        if summary != "":
            self._publish.append(
                dict({"name": name, "summary": summary, "loop": loop, "paras": paras}))

        return name
