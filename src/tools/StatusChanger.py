from Tool import Tool
import httpx
import concurrent.futures
from utils import Utils

class StatusChanger(Tool):
    def __init__(self, app):
        super().__init__("Status Changer", "Change the status of a large number of accounts", 7, app)

    def run(self):
        new_status = input("New status: ")

        cookies = self.get_cookies()

        req_worked = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.change_status, new_status, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_changed, response_text = future.result()
                except Exception as e:
                    is_changed, response_text = False, str(e)

                if is_changed:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, is_changed, "Changed")

    @Utils.retry_on_exception()
    def change_status(self, new_status, cookie):
        """
        Changes the status of a user
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        req_url = "https://accountinformation.roblox.com/v1/description"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token, "application/x-www-form-urlencoded")
        req_data = {"description": new_status }

        response = httpx.post(req_url, headers=req_headers, cookies=req_cookies, data=req_data, proxies=proxies)

        return (response.status_code == 200), response.text
