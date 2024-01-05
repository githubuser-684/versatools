import httpc
from Tool import Tool
import concurrent.futures
from utils import Utils
import threading
import click
from RobloxClient import RobloxClient

class GameVote(Tool):
    def __init__(self, app):
        super().__init__("Game Vote", "Increase Like/Dislike count of a game", app)

    def run(self):
        game_id = self.config["game_id"]
        timeout = self.config["timeout"]
        vote = not self.config["dislike"]
        cookies = self.get_cookies(self.config["max_generations"])
        max_workers = self.config["max_workers"]

        click.secho("Warning: on Windows 11, it may not be possible to run multiple roblox instances", fg="yellow")

        roblox_player_path = RobloxClient.find_roblox_player()

        if max_workers == None or max_workers > 1:
            threading.Thread(target=Tool.run_until_exit, args=(RobloxClient.remove_singleton_mutex,)).start()

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as self.executor:
            self.results = [self.executor.submit(self.send_game_vote, game_id, vote, cookie, roblox_player_path, timeout) for cookie in cookies]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue

                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "New votes")

    @Utils.handle_exception(3)
    def send_game_vote(self, game_id, vote, cookie, roblox_player_path, timeout):
        """
        Send a vote to a game
        """
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            rblx_client = RobloxClient(roblox_player_path)
            auth_ticket = rblx_client.get_auth_ticket(cookie, user_agent, csrf_token)
            rblx_client.launch_place(auth_ticket, game_id, timeout)

            req_url = f"https://www.roblox.com/voting/vote?assetId={game_id}&vote={'true' if vote else 'false'}"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)

            response = client.post(req_url, headers=req_headers, cookies=req_cookies)

        try:
            success = (response.status_code == 200 and response.json()["Success"])
        except KeyError:
            raise Exception("Failed to access Success key. " + Utils.return_res(response))

        return success, Utils.return_res(response)
