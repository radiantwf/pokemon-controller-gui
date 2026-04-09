import multiprocessing
from runtime_bootstrap import bootstrap_runtime


bootstrap_runtime()

import ui

def main():
    ui.run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
