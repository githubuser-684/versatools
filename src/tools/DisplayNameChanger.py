import time
import requests
from Tool import Tool
import concurrent.futures

class DisplayNameChanger(Tool):
    def __init__(self, app):
        super().__init__("Display Name Changer", "Change Display Name of your bots", 3, app)
        
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

        self.cookies_file_path = self.app.cookies_file_path

    def run(self):
        print("\033[1;31mWarning: Display names can only be changed once every week\033[0;30m")
        new_display_name = input("New display name: ")
            
        f = open(self.cookies_file_path, 'r+')
        cookies = f.read().splitlines()
        f.close()

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.change_display_name, new_display_name, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                is_success, response_text = future.result()

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                print("\033[1A\033[K\033[1A\033[K\033[1;32mChanged: "+str(req_sent)+"\033[0;0m | \033[1;31mFailed: "+str(req_failed)+"\033[0;0m | \033[1;34mTotal: "+str(total_req) + "\033[0;0m")
                print("\033[1;32mWorked: " + response_text + "\033[0;0m" if is_success else "\033[1;31mFailed: " + response_text + "\033[0;0m")
    
    def change_display_name(self, new_display_name, cookie):
        err = None
        for _ in range(3):
            try:
                proxies = self.get_random_proxies() if self.use_proxy else None
                user_agent = self.get_random_user_agent()
                csrf_token = self.get_csrf_token(proxies, cookie)
                user_id, username, robux_balance, thumbnail_url, is_any_builders_club_member, is_premium = self.get_user_info(cookie, proxies, user_agent)

                req_url = f"https://users.roblox.com:443/v1/users/{user_id}/display-names"
                req_cookies = {".ROBLOSECURITY": cookie}
                req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
                req_json = {"newDisplayName": new_display_name}

                response = requests.patch(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)
                break
            except Exception as e:
                err = str(e)
                time.sleep(2)
        else:
            return False, err
        
        
        return (response.status_code == 200), response.text