import os
import concurrent.futures
import httpx
import eel
from Tool import Tool
from utils import Utils

class RegionUnlocker(Tool):
    def __init__(self, app):
        super().__init__("Region Unlocker", "Unlock the region of your cookies", 3, app)

        self.unlocked_cookies_file_path = os.path.join(self.files_directory, "unlocked-cookies.txt")

    def run(self):
        cookies = self.get_cookies()

        eel.write_terminal("\x1B[1;33mWarning: your cookies will be exposed to rbxfresh.net for unlocking, so make sure to trust them.\x1B[0;0m")

        f = open(self.unlocked_cookies_file_path, 'w')
        f.seek(0)
        f.truncate()

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.unlock_cookie, cookie, self.config["use_proxy"]) for cookie in cookies]

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

                self.print_status(req_sent, req_failed, total_req, response_text, has_worked, "Unlocked")

        f.close()

        # replace cookies
        f = open(self.cookies_file_path, 'w')
        f.seek(0)
        f.truncate()
        f.write(open(self.unlocked_cookies_file_path, 'r').read())

        os.remove(self.unlocked_cookies_file_path)

    @Utils.handle_exception()
    def unlock_cookie(self, cookie:str, use_proxy:bool) -> str:
        """
        Unlock a ROBLOSECURITY cookie
        """
        proxies = self.get_random_proxies() if use_proxy else None

        with httpx.Client(proxies=proxies) as client:
            # Refresh using rbxfresh.net
            req_url = "https://rbxfresh.net/refresh"
            req_headers = {
                "User-Agent": self.get_random_user_agent(),
                "Content-Type": "application/x-www-form-urlencoded",
            }
            req_data = {
                "cookie": cookie,
            }

            res = client.post(req_url, headers=req_headers, data=req_data)

            if "_|WARNING:-DO-NOT-SHARE" not in res.text:
                raise Exception(res.text)

            cookie = res.text

        return cookie
