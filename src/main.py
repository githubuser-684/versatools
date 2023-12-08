# fix: https://stackoverflow.com/questions/75232011/why-does-exe-built-using-pyinstaller-isnt-working
import sys
import io

buffer = io.StringIO()
sys.stdout = sys.stderr = buffer

# pylint: disable=wrong-import-position
from multiprocessing import freeze_support
from App import App
from App import show_menu
import eel
from threading import Thread

if __name__ == "__main__":
    freeze_support() # needed for multiprocessing on windows

    app = App()

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
        eel.start('update.html', port=3042, size=(500, 500))
    else:
        show_menu()
        app.set_proxies_loaded()
        app.set_cookies_loaded()

        eel.start('index.html', port=3043, size=(1425, 885))
