from App import App
from multiprocessing import freeze_support
import signal
import os

def signal_handler(sig, frame):
    print('\nBye!')
    os.kill(os.getpid(), 9)

if __name__ == "__main__":
    freeze_support() # needed for multiprocessing on windows
    signal.signal(signal.SIGINT, signal_handler)

    app = App()
    app.run()