from Tool import Tool
import discordRpc
import time
from time import mktime
import eel

class DiscordRpc(Tool):
    def __init__(self, app):
        super().__init__("Discord RPC", "Change your discord status!", 6, app)

    def run(self):
        client_id = self.config["client_id"]
        rpc_obj = discordRpc.DiscordIpcClient.for_platform(client_id)
        eel.write_terminal("RPC connection successful.")

        time.sleep(5)
        start_time = mktime(time.localtime())
        while True:
            activity = {
                    "state": self.config["state"],
                    "details": self.config["details"],
                    "timestamps": {
                        "start": start_time
                    },
                    "assets": {
                        "small_text": self.config["small_text"],
                        "small_image": self.config["small_image"],
                        "large_text": self.config["large_text"],
                        "large_image": self.config["large_image"]
                    }
                }
            rpc_obj.set_activity(activity)
            time.sleep(900)