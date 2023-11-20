import os
import concurrent.futures
import httpx
import re
from Tool import Tool
from utils import Utils

class CookieRefresher(Tool):
    def __init__(self, app):
        super().__init__("Cookie Refresher", "Refresh your .ROBLOSECURITY cookies!", 7, app)

        self.new_cookies_file_path = os.path.join(self.files_directory, "refreshed-cookies.txt")

    @Tool.handle_exit
    def run(self):
        cookies, lines = self.get_cookies(None, True)

        f = open(self.new_cookies_file_path, 'w')
        f.seek(0)
        f.truncate()

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.refresh_cookie, cookie, self.config["use_proxy"]) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    has_worked, response_text, old_cookie = future.result()
                except Exception as err:
                    has_worked, response_text = False, str(err)

                if has_worked:
                    req_sent += 1
                    cookie = response_text

                    # search for the user:pass: part of the line
                    pattern = re.compile(rf'(.*?){re.escape(old_cookie)}.*')
                    matched_lines = [pattern.search(line) for line in lines if pattern.search(line)]
                    user_pass_part = matched_lines[0].group(1)

                    f.write(user_pass_part+cookie+"\n")
                    f.flush()
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, has_worked, "Refreshed")

        f.close()

        # replace cookies
        f = open(self.cookies_file_path, 'w')
        f.seek(0)
        f.truncate()
        f.write(open(self.new_cookies_file_path, 'r').read())

        os.remove(self.new_cookies_file_path)

    @Utils.handle_exception()
    def refresh_cookie(self, cookie:str, use_proxy:bool):
        proxies = self.get_random_proxies() if use_proxy else None

        with httpx.Client(proxies=proxies) as client:
            user_agent = self.get_random_user_agent()
            xcsrf_token = self.get_csrf_token(cookie, client)

            # Creating a new cookie
            reauthcookieurl = "https://www.roblox.com/authentication/signoutfromallsessionsandreauthenticate"
            req_headers = self.get_roblox_headers(user_agent, xcsrf_token)

            data = client.post(reauthcookieurl, cookies={'.ROBLOSECURITY': cookie}, headers=req_headers)

        try:
            new_cookie = data.headers["Set-Cookie"].split(".ROBLOSECURITY=")[1].split(";")[0]
        except Exception:
            raise Exception(Utils.return_res(data))

        return True, new_cookie, cookie
