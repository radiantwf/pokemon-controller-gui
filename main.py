import multiprocessing
import sys

sys.path.append('./src')
import ui

def main():
    ui.run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
