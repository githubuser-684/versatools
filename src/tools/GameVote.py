import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils

class GameVote(Tool):
    def __init__(self, app):
        super().__init__("Game Vote", "Increase Like/Dislike count of a game", 1, app)

    @Tool.handle_exit
    def run(self):
        game_id = self.config["game_id"]
        vote = not self.config["dislike"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_game_vote, game_id, vote, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
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
    def send_game_vote(self, game_id, vote, cookie):
        """
        Send a vote to a game
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None

        with httpx.Client(proxies=proxies) as client:
            user_agent = self.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = f"https://www.roblox.com/voting/vote?assetId={game_id}&vote={'true' if vote else 'false'}"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = self.get_roblox_headers(user_agent, csrf_token)

            response = client.post(req_url, headers=req_headers, cookies=req_cookies)

        try:
            success = (response.status_code == 200 and response.json()["Success"])
        except Exception:
            raise Exception("Failed to access Success key. " + Utils.return_res(response))

        return success, Utils.return_res(response)
