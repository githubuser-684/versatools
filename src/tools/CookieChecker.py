import os
import concurrent.futures
import httpc
import re
from Tool import Tool
from utils import Utils

class CookieChecker(Tool):
    def __init__(self, app):
        super().__init__("Cookie Checker", "Checks if cookies are valid and shuffle and unduplicate them.", app)

        self.cache_file_path = os.path.join(self.cache_directory, "verified-cookies.txt")

    def run(self):
        cookies, lines = self.get_cookies(None, True)

        if self.config["delete_invalid_cookies"]:
            f = open(self.cache_file_path, 'w')
            f.seek(0)
            f.truncate()

        working_cookies = 0
        failed_cookies = 0
        total_cookies = len(cookies)

        # for each line, test the proxy
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.test_cookie, cookie, self.config["use_proxy"]) for cookie in cookies]

            for future in concurrent.futures.as_completed(self.results):
                try:
                    is_working, cookie, response_text = future.result()
                except Exception as e:
                    is_working, response_text = False, str(e)

                if is_working:
                    working_cookies += 1
                else:
                    failed_cookies += 1

                if self.config["delete_invalid_cookies"] and is_working:
                    # write line that contains cookie
                    pattern = re.compile(rf'.*{re.escape(cookie)}.*')
                    matched_lines = [line for line in lines if pattern.search(line)]
                    matched_line = matched_lines[0]

                    f.write(matched_line + "\n")
                    f.flush()

                self.print_status(working_cookies, failed_cookies, total_cookies, response_text, is_working, "Working")

        if self.config["delete_invalid_cookies"]:
            f.close()

            # replace file with cache
            with open(self.cookies_file_path, 'w') as destination_file:
                with open(self.cache_file_path, 'r') as source_file:
                    destination_file.seek(0)
                    destination_file.truncate()
                    destination_file.write(source_file.read())

    @Utils.handle_exception(2)
    def test_cookie(self, cookie, use_proxy):
        """
        Checks if a cookie is working
        """
        proxies = self.get_random_proxy() if use_proxy else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            req_url = "https://www.roblox.com/mobileapi/userinfo"
            req_cookies = { ".ROBLOSECURITY": cookie }
            req_headers = httpc.get_roblox_headers(user_agent)

            response = client.get(req_url, headers=req_headers, cookies=req_cookies)

            if "NewLogin" in response.text:
                return False, cookie, Utils.return_res(response)

            if response.status_code != 200:
                raise Exception(Utils.return_res(response))

            result = response.json()
            user_id = result["UserID"]
            username = result["UserName"]
            robux_balance = result["RobuxBalance"]

            has_premium = False

            stringConstruct = f"UserID: {user_id} | Username: {username} | Robux Balance: {robux_balance} "

            if self.config["check_premium"]:
                premium_url = f"https://www.roblox.com/users/{user_id}/profile"
                premium_response = client.get(premium_url, headers=req_headers, cookies=req_cookies)

                if "data-ispremiumuser=\"true\"" in premium_response.text:
                    has_premium = True
                    stringConstruct += "| Premium: True"
                else:
                    stringConstruct += "| Premium: False"
                    
            return True, cookie, f"{stringConstruct}"