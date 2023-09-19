import os
import concurrent.futures
import httpx
from Tool import Tool
from utils import Utils

class CookieRefresher(Tool):
    def __init__(self, app):
        super().__init__("Cookie Refresher", "Refresh your .ROBLOSECURITY cookies!", 7, app)

        self.new_cookies_file_path = os.path.join(self.files_directory, "refreshed-cookies.txt")

    def run(self):
        cookies = self.get_cookies()

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
                    cookie = future.result()
                    req_sent += 1
                    f.write(cookie+"\n")
                    f.flush()
                    response_text = cookie
                    has_worked = True
                except Exception as err:
                    has_worked = False
                    req_failed += 1
                    response_text = str(err)

                self.print_status(req_sent, req_failed, total_req, response_text, has_worked, "Generated")

        f.close()
        os.replace(self.new_cookies_file_path, self.cookies_file_path)

    @Utils.retry_on_exception(1)
    def refresh_cookie(self, cookie:str, use_proxy:bool) -> tuple:
        """
        Refresh a ROBLOSECURITY cookie
        Returns a tuple with the error and the new cookie
        """
        user_agent = self.get_random_user_agent()
        proxies = self.get_random_proxies() if use_proxy else None
        xcsrf_token = self.get_csrf_token(proxies, cookie)

        # Creating a new cookie
        reauthcookieurl = "https://www.roblox.com/authentication/signoutfromallsessionsandreauthenticate"
        req_headers = self.get_roblox_headers(user_agent, xcsrf_token)

        data = httpx.post(reauthcookieurl, cookies={'.ROBLOSECURITY': cookie}, headers=req_headers, proxies=proxies)
        cookie = data.headers.get("Set-Cookie").split(".ROBLOSECURITY=")[1].split(";")[0]

        return cookie
