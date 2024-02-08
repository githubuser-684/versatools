import os
import concurrent.futures
import httpc
from Tool import Tool
from CaptchaSolver import CaptchaSolver
from utils import Utils

class UP2UPC(Tool):
    def __init__(self, app):
        super().__init__("UP Converter", "Convert user password list to UPC format", app)

        self.user_pass_file_path = os.path.join(self.files_directory, "user-pass.txt")
        Utils.ensure_files_exist([self.user_pass_file_path])

    def run(self):
        user_pass_list = self.get_user_pass()

        if len(user_pass_list) == 0:
            raise Exception("No user-pass found in files/user-pass.txt")

        f = open(self.cookies_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = len(user_pass_list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.convert_up, self.config["captcha_solver"], self.config["use_proxy"], user_pass) for user_pass in user_pass_list]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue

                try:
                    has_converted, response_text = future.result()
                except Exception as e:
                    has_converted, response_text = False, str(e)

                if has_converted:
                    worked_gen += 1
                    f.write(response_text+"\n")
                    f.flush()
                else:
                    failed_gen += 1

                self.print_status(worked_gen, failed_gen, total_gen, response_text, has_converted, "Converted")
        f.close()

    def get_user_pass(self) -> list:
        f = open(self.user_pass_file_path, 'r')
        lines = f.read().splitlines()
        f.close()

        # ignore duplicates
        user_pass_list = [*set(lines)]

        return user_pass_list

    @Utils.handle_exception(3, False)
    def send_signin_request(self, username, password, user_agent, csrf_token, client):
        req_url = "https://auth.roblox.com/v2/login"
        req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
        req_json={
            "ctype": "Username",
            "cvalue": username,
            "password": password
        }
        result = client.post(req_url, headers=req_headers, json=req_json)

        return result

    @Utils.handle_exception()
    def convert_up(self, captcha_service, use_proxy, user_pass) -> tuple:
        proxies, proxy_line = self.get_random_proxy(line=True) if use_proxy else (None, None)
        username, password = user_pass.split(":")

        with httpc.Session(proxies=proxies, spoof_tls=True) as client:
            captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens.get(captcha_service))
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(None, client)

            sign_in_req = self.send_signin_request(username, password, user_agent, csrf_token, client)

            sign_in_res = captcha_solver.solve_captcha(sign_in_req, "ACTION_TYPE_WEB_LOGIN", proxy_line, client)

        try:
            cookie = httpc.extract_cookie(sign_in_res, ".ROBLOSECURITY")
        except Exception:
            raise Exception(Utils.return_res(sign_in_res))

        return True, f"{username}:{password}:{cookie}"
