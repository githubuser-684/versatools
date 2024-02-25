from Tool import Tool
from utils import Utils
import concurrent.futures
import threading
import click
from RobloxClient import RobloxClient
import httpc

class GameVisits(Tool):
    def __init__(self, app):
        super().__init__("Game Visits", "Boost game visits", app)

    def run(self):
        max_generations = self.config["max_generations"]
        timeout = self.config["timeout"]
        place_id = self.config["place_id"]
        max_workers = self.config["max_workers"]

        click.secho("Warning: on Windows 11, it may not be possible to run multiple roblox instances", fg="yellow")

        roblox_player_path = RobloxClient.find_roblox_player()

        if max_workers == None or max_workers > 1:
            threading.Thread(target=Tool.run_until_exit, args=(RobloxClient.remove_singleton_mutex,)).start()

        req_sent = 0
        req_failed = 0
        total_req = max_generations

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as self.executor:
            self.results = [self.executor.submit(self.visit_game, roblox_player_path, self.get_random_cookie(), place_id, timeout) for i in range(max_generations)]

            for future in concurrent.futures.as_completed(self.results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "New visits")

    @Utils.handle_exception()
    def visit_game(self, roblox_player_path, cookie, place_id, timeout):
        csrf_token = self.get_csrf_token(cookie)
        user_agent = httpc.get_random_user_agent()

        rblx_client = RobloxClient(roblox_player_path)
        auth_ticket = rblx_client.get_auth_ticket(cookie, user_agent, csrf_token)
        rblx_client.launch_place(auth_ticket, place_id, timeout)

        return True, "Cookie visited the game"