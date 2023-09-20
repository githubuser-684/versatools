import httpx
from Tool import Tool
import concurrent.futures
from CaptchaSolver import CaptchaSolver
from data.comments import comments
import random

class CommentBot(Tool):
    def __init__(self, app):
        super().__init__("Comment Bot", "Increase/Decrease comments count of an asset", 2, app)

    def run(self):
        asset_id = self.config["asset_id"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_comment, self.config["captcha_solver"], asset_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as err:
                    is_success, response_text = False, str(err)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "Commented")

    def get_random_message(self):
        """
        Get a random message from the comments list
        """
        return random.choice(comments)

    def send_comment(self, captcha_service, asset_id, cookie):
        """
        Send a comment to an asset
        """
        captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        req_url = "https://www.roblox.com/comments/post"
        req_cookies = { ".ROBLOSECURITY": cookie }
        req_headers = self.get_roblox_headers(user_agent, csrf_token, "application/x-www-form-urlencoded")
        req_data = {"assetId": str(asset_id), "text": self.get_random_message()}

        init_res = httpx.post(req_url, headers=req_headers, data=req_data, cookies=req_cookies, proxies=proxies)
        response = captcha_solver.solve_captcha(init_res, "ACTION_TYPE_ASSET_COMMENT", user_agent, proxies)

        return (response.status_code == 200 and response.get('ErrorCode') is None), response.text
