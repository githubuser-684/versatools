import httpc
from Tool import Tool
import concurrent.futures
from CaptchaSolver import CaptchaSolver
from utils import Utils

class FollowBot(Tool):
    def __init__(self, app):
        super().__init__("Follow Bot", "Increase Followers count of a user", 4, app)

    @Tool.handle_exit
    def run(self):
        user_id = self.config["user_id"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_worked = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_follow_request, self.config["captcha_solver"], user_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_followed, response_text = future.result()
                except Exception as e:
                    is_followed, response_text = False, str(e)

                if is_followed:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, is_followed, "New followers")

    @Utils.handle_exception()
    def send_follow_request(self, captcha_service:str, user_id:str | int, cookie:str):
        """
        Send a follow request to a user
        """
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies, spoof_tls=True) as client:
            captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = f"https://friends.roblox.com/v1/users/{user_id}/follow"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
            del req_headers["Content-Type"]

            init_res = client.post(req_url, headers=req_headers, cookies=req_cookies)

            response = captcha_solver.solve_captcha(init_res, "ACTION_TYPE_FOLLOW_USER", client)

        return (response.status_code == 200), Utils.return_res(response)
