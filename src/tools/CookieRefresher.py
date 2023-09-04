import os
import concurrent.futures
import requests
from Tool import Tool
from utils import Utils

class CookieRefresher(Tool):
    def __init__(self, app):
        super().__init__("Cookie Refresher", "Refresh your .ROBLOSECURITY cookies!", 7, app)

        self.use_proxy = self.config["use_proxy"]
        self.max_workers = self.config["max_workers"]

        self.new_cookies_file_path = os.path.join(self.files_directory, "refreshed-cookies.txt")

    def run(self):
        cookies = self.get_cookies()

        f = open(self.new_cookies_file_path, 'w')
        f.seek(0)
        f.truncate()

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.refresh_cookie, cookie, self.use_proxy) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    cookie = future.result()
                    req_sent += 1
                    f.write(cookie+"\n")
                    response_text = cookie
                except Exception as e:
                    error = str(e)
                    req_failed += 1
                    response_text = error

                self.print_status(req_sent, req_failed, total_req, response_text, error == None, "Generated")

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
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": xcsrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

        data = requests.post(reauthcookieurl, cookies={'.ROBLOSECURITY': cookie}, headers=req_headers, proxies=proxies)
        cookie = data.headers.get("Set-Cookie").split(".ROBLOSECURITY=")[1].split(";")[0]

        return cookie