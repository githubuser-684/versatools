import sys
import os
import subprocess as sps
# redirect stdout, stderr and stdin to logs.txt
# this is needed as the app is consoleless
if hasattr(sys, "_MEIPASS"):
    with open(os.path.join(os.path.dirname(__file__), "./logs.txt"), "a") as f_logs:
        sys.stdout = f_logs
        sys.stderr = f_logs
        sps.PIPE = f_logs

from multiprocessing import freeze_support
from App import App
from App import show_menu
import eel
from threading import Thread
import win32event
import win32api
import winerror

def start_eel(start_url, **kwargs):
    args = {
        "port": 3042,
        "size": (1425, 885)
    }

    args.update(kwargs)

    try:
        eel.start(start_url, **args)
    except EnvironmentError:
        eel.start(start_url, mode='edge', **args)

if __name__ == "__main__":
    freeze_support() # needed for multiprocessing on windows

    # add mutex to prevent multiple instances of the app
    win32_mutex = win32event.CreateMutex(None, 1, "VersatoolsMutex")
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        raise Exception("Another instance of Versatools is already running")

    app = App()

    @eel.expose
    def get_cookies_loaded():
        return app.get_cookies_loaded()

    @eel.expose
    def get_proxies_loaded():
        return app.get_proxies_loaded()

    @eel.expose
    def launch_app_tool(tool_name):
        thread = Thread(target=lambda: app.launch_tool(tool_name))
        thread.start()

    @eel.expose
    def stop_current_tool():
        app.current_tool.signal_handler()

    @eel.expose
    def get_tool_config(tool_name):
        return app.get_tool_config(tool_name)

    @eel.expose
    def set_tool_config(tool_name, config):
        return app.set_tool_config(tool_name, config)

    @eel.expose
    def update_versatools():
        return app.update_versatools()

    eel.init('src/web')

    is_update_available = app.check_update()

    if is_update_available:
        start_eel('update.html', size=(500, 500))
    else:
        show_menu()

        start_eel('index.html')
