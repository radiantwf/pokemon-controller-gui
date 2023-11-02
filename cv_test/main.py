import multiprocessing
import sys

import ui

def main():
    ui.run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
