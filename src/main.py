from App import App
from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support() # needed for multiprocessing on windows

    app = App()
    app.run()