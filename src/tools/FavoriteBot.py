import httpx
from Tool import Tool
import concurrent.futures
import time
from utils import Utils

class FavoriteBot(Tool):
    def __init__(self, app):
        super().__init__("Favorite Bot", "Increase/Decrease stars count of an asset", 2, app)

    def run(self):
        asset_id = input("Asset ID to favorite/unfavorite: ")
        unfavorite = input('Enter "a" to unfavorite: ') == "a"

        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_favorite, asset_id, cookie, unfavorite) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "New favorites")

    @Utils.retry_on_exception()
    def send_favorite(self, asset_id, cookie, unfavorite: bool):
        """
        Send a favorite to an asset
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)
        user_info = self.get_user_info(cookie, proxies, user_agent)
        user_id = user_info.get("UserID")

        send = httpx.delete if unfavorite else httpx.post

        req_url = f"https://catalog.roblox.com/v1/favorites/users/{user_id}/assets/{asset_id}/favorite"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)

        response = send(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)

        time.sleep(self.config["timeout"])

        return (response.status_code == 200), response.text
