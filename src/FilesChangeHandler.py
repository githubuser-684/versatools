from watchdog.events import FileSystemEventHandler
import eel

class FilesChangeHandler(FileSystemEventHandler):
    """
    Handles files/* changes
    """
    def __init__(self, app):
        self.app = app

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('config.json'):
            self.app.set_tool_config_ui()
        elif event.src_path.endswith('cookies.txt'):
            eel.reload_cookies()()
        elif event.src_path.endswith('proxies.txt'):
            eel.reload_proxies()()
