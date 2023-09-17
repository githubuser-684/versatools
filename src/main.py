from multiprocessing import freeze_support
from App import App

if __name__ == "__main__":
    freeze_support() # needed for multiprocessing on windows

    app = App()
    app.run()
