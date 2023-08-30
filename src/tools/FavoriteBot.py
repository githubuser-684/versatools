import requests
from Tool import Tool
import concurrent.futures
import time

class FavoriteBot(Tool):
    def __init__(self, app):
        super().__init__("Favorite Bot", "Increase/Decrease stars count of an asset", 2, app)
        
        self.max_generations = self.config["max_generations"]
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]
        self.timeout = self.config["timeout"]

        self.cookies_file_path = self.app.cookies_file_path

    def run(self):
        asset_id = input("Asset ID to favorite/unfavorite: ")
        
        unfavorite = input('Enter "a" to unfavorite: ') == "a"
    
        f = open(self.cookies_file_path, 'r+')
        cookies = f.read().splitlines()
        f.close()

        if self.max_generations < len(cookies):
            cookies = cookies[:self.max_generations]
            
        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.send_favorite, asset_id, cookie, unfavorite) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                is_success, response_text = future.result()

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                print("\033[1A\033[K\033[1A\033[K\033[1;32mNew Favorites: "+str(req_sent)+"\033[0;0m | \033[1;31mFailed: "+str(req_failed)+"\033[0;0m | \033[1;34mTotal: "+str(total_req) + "\033[0;0m")
                print("\033[1;32mWorked: " + response_text + "\033[0;0m" if is_success else "\033[1;31mFailed: " + response_text + "\033[0;0m")
    
    def send_favorite(self, asset_id, cookie, unfavorite: bool):
        err = None
        for _ in range(3):
            try:
                proxies = self.get_random_proxies() if self.use_proxy else None
                user_agent = self.get_random_user_agent()
                csrf_token = self.get_csrf_token(proxies, cookie)
                user_id, username, robux_balance, thumbnail_url, is_any_builders_club_member, is_premium = self.get_user_info(cookie, proxies, user_agent)
                send = requests.delete if unfavorite else requests.post

                req_url = f"https://catalog.roblox.com:443/v1/favorites/users/{user_id}/assets/{asset_id}/favorite"
                req_cookies = {".ROBLOSECURITY": cookie}
                req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

                response = send(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)
                break
            except Exception as e:
                err = str(e)
                time.sleep(2)
        else:
            return False, err
        
        # wait for 1 second
        time.sleep(self.timeout)
    
        return (response.status_code == 200), response.text