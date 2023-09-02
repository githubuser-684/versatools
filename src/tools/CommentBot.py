import requests
from Tool import Tool
import concurrent.futures
from CaptchaSolver import CaptchaSolver

class CommentBot(Tool):
    def __init__(self, app):
        super().__init__("Comment Bot", "Increase/Decrease comments count of an asset", 2, app)
        
        self.max_generations = self.config["max_generations"]
        self.captcha_solver = self.config["captcha_solver"]
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

    def run(self):
        asset_id = input("Asset ID to comment: ")    
        cookies = self.get_cookies(self.max_generations)

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.send_comment, self.captcha_solver, asset_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                is_success, response_text = future.result()

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                print("\033[1A\033[K\033[1A\033[K\033[1;32mNew comment: "+str(req_sent)+"\033[0;0m | \033[1;31mFailed: "+str(req_failed)+"\033[0;0m | \033[1;34mTotal: "+str(total_req) + "\033[0;0m")
                print("\033[1;32mWorked: " + response_text + "\033[0;0m" if is_success else "\033[1;31mFailed: " + response_text + "\033[0;0m")
    
    def send_comment(self, captcha_service, asset_id, cookie):
        err = None
        for _ in range(3):
            try:
                captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
                proxies = self.get_random_proxies() if self.use_proxy else None
                user_agent = self.get_random_user_agent()
                csrf_token = self.get_csrf_token(proxies, cookie)

                req_url = "https://www.roblox.com/comments/post"
                req_cookies = { ".ROBLOSECURITY": cookie }
                req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/x-www-form-urlencoded", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
                req_data = {"assetId": str(asset_id), "text": "cute"}
                init_res = requests.post(req_url, headers=req_headers, data=req_data, cookies=req_cookies, proxies=proxies)

                response = captcha_solver.solve_captcha(init_res, "ACTION_TYPE_ASSET_COMMENT", user_agent, csrf_token, proxies)
                break
            except Exception as e:
                err = str(e)
        else:
            return False, err
    
        return (response.status_code == 200), response.text