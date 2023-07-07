
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
            script = macro.published()
            self._macro_list = json.loads(script)
            MacroLauncher._first = False
            self._macro_process = None

    def list_macro(self):
        return self._macro_list
    
    def macro_run(self, macro_name: str, loop: int = 1, paras: dict = dict(), port: int = 50000):
        self.stop()

        self._macro_process = multiprocessing.Process(
            target=macro.run, args=(macro_name, loop, paras, port))
        self._macro_process.start()

    
    def macro_stop(self):
        if self._macro_process != None:
            try:
                self._macro_process.terminate()
                self._macro_process.join(1)
                self._macro_process = None
            except:
                self._macro_process.kill()
                self._macro_process = None
    
    def macro_running(self):
        if self._macro_process != None:
            return self._macro_process.is_alive()
        return False
