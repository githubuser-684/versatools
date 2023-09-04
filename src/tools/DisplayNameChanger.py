import requests
from Tool import Tool
import concurrent.futures
from utils import Utils

class DisplayNameChanger(Tool):
    def __init__(self, app):
        super().__init__("Display Name Changer", "Change Display Name of your bots", 3, app)
        
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

    def run(self):
        print("\033[1;31mWarning: Display names can only be changed once every week\033[0;0m")
        new_display_name = input("New display name: ")
            
        cookies = self.get_cookies()

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.change_display_name, new_display_name, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)
                
                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "Changed")

    @Utils.retry_on_exception()
    def change_display_name(self, new_display_name, cookie):
        proxies = self.get_random_proxies() if self.use_proxy else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)
        user_info = self.get_user_info(cookie, proxies, user_agent)
        user_id = user_info.get("UserID")

        req_url = f"https://users.roblox.com/v1/users/{user_id}/display-names"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        req_json = {"newDisplayName": new_display_name}

        response = requests.patch(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)

        return (response.status_code == 200), response.text