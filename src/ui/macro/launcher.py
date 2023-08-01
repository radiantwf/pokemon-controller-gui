
import json
import multiprocessing
import sys

sys.path.append('./src')
import macro

class MacroLauncher(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(MacroLauncher, cls).__new__(cls)
        return cls._instance

    _first = True

    def __init__(self):
        if MacroLauncher._first:
            self._macro_list = dict()
            MacroLauncher._first = False
            self._macro_process = None
            self._stop_event = None

    def list_macro(self):
        script = macro.published()
        self._macro_list = json.loads(script)
        return self._macro_list
    
    def macro_start(self, macro_name: str, controller_input_action_queue: multiprocessing.Queue, loop: int = 1, paras: dict = dict()):
        self.macro_stop()
        self._stop_event = multiprocessing.Event()
        self._macro_process = multiprocessing.Process(
            target=macro.run, args=(macro_name, self._stop_event, controller_input_action_queue, loop, paras))
        self._macro_process.start()

    
    def macro_stop(self,timeout = 10):
        if self._macro_process != None:
            try:
                self._stop_event.set()
                self._macro_process.join(timeout)
                if self._macro_process.is_alive():
                    self._macro_process.terminate()
                else:
                    self._macro_process = None
                    return True
            except:
                self._macro_process.terminate()
            self._macro_process = None
            return False
        return True
    
    def macro_running(self):
        if self._macro_process != None:
            return self._macro_process.is_alive()
        return False
