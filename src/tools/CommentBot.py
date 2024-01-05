import httpc
from Tool import Tool
import concurrent.futures
from CaptchaSolver import CaptchaSolver
from data.comments import comments
import random
from utils import Utils

class CommentBot(Tool):
    def __init__(self, app):
        super().__init__("Comment Bot", "Increase/Decrease comments count of an asset", app)

    def run(self):
        asset_id = self.config["asset_id"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.send_comment, self.config["captcha_solver"], asset_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue

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

    @Utils.handle_exception()
    def send_comment(self, captcha_service, asset_id, cookie):
        """
        Send a comment to an asset
        """
        captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies, spoof_tls=True) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = "https://www.roblox.com/comments/post"
            req_cookies = { ".ROBLOSECURITY": cookie }
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token, "application/x-www-form-urlencoded; charset=UTF-8")
            req_data = {"assetId": str(asset_id), "text": self.get_random_message()}

            init_res = client.post(req_url, headers=req_headers, data=req_data, cookies=req_cookies)
            response = captcha_solver.solve_captcha(init_res, "ACTION_TYPE_ASSET_COMMENT", client)

        success = response.status_code == 200

        return success, Utils.return_res(response)
