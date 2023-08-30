import os
import time
import random
import concurrent.futures
import requests
from Tool import Tool

class CookieChecker(Tool):
    def __init__(self, app):
        super().__init__("Cookie Checker", "Checks if cookies are valid and shuffle and unduplicate them.", 1, app)

        self.file_path = self.app.cookies_file_path
        self.cache_file_path = os.path.join(self.cache_directory, "verified-cookies.txt")
    
    def run(self):
        delete_invalid_cookies = self.config["delete_invalid_cookies"]
        use_proxy = self.config["use_proxy"]
        max_workers = self.config["max_workers"]
        
        f = open(self.file_path, 'r+')
        lines = f.read().splitlines()
        f.close()
        # remove duplicates
        lines = [*set(lines)]
        # shuffle
        random.shuffle(lines)

        unduplicate_only = input("Enter 'a' if you want ONLY to unduplicate and mix cookies: ")
        if (unduplicate_only == "a"):
            f = open(self.file_path, 'w')
            f.seek(0)
            f.truncate()
            for line in lines:
                f.write(line + "\n")
            f.close()
            return

        f = open(self.cache_file_path, 'w')
        f.seek(0)
        f.truncate()

        working_cookies = 0
        failed_cookies = 0
        total_cookies = len(lines)

        print("Please wait... \n ")

        # for each line, test the proxy
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = [executor.submit(self.test_cookie, line, use_proxy) for line in lines]

            for future in concurrent.futures.as_completed(results):
                is_working, cookie, user_id, username, robux_balance, error = future.result()

                if is_working:
                    working_cookies += 1
                else:
                    failed_cookies += 1
                
                if not (delete_invalid_cookies and not is_working):
                    f.write(cookie + "\n") 

                print("\033[1A\033[K\033[1A\033[K\033[1;32mWorking: "+str(working_cookies)+"\033[0;0m | \033[1;31mFailed: "+str(failed_cookies)+"\033[0;0m | \033[1;34mTotal: "+str(total_cookies) + "\033[0;0m")
                print("\033[1;32mWorked: UserID: " + str(user_id) + " Username: " + username + " Robux Balance: " + str(robux_balance) + "\033[0;0m" if is_working else f"\033[1;31m{error}\033[0;0m")          

        f.close()
        os.replace(self.cache_file_path, self.file_path)

    def test_cookie(self, cookie, use_proxy):
        for _ in range(10):
            try:
                user_agent = self.get_random_user_agent()
                proxies = self.get_random_proxies() if use_proxy else None

                req_url = "https://www.roblox.com:443/mobileapi/userinfo"
                req_cookies = { ".ROBLOSECURITY": cookie }
                req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

                response = requests.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)
                break
            except:
                time.sleep(2)
        else:
            return False, cookie, None, None, None, "Error testing cookie. too many tries"

        try:
            result = response.json()

            user_id = result["UserID"]
            username = result["UserName"]
            robux_balance = result["RobuxBalance"]
        except Exception as e:
            return False, cookie, None, None, None, str(e)

        return True, cookie, user_id, username, robux_balance, None