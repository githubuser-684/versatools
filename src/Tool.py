import json
import random
import httpx
from abc import ABC, abstractmethod
from Proxy import Proxy
from fake_useragent import UserAgent

class Tool(Proxy, ABC):
    def __init__(self, name: str, description: str, color: int, app: object):
        super().__init__()

        self.color = color
        self.name = name
        self.description = description
        self.app = app

        self.config = {}
        self.captcha_tokens = {}

        # file paths
        self.cache_directory = app.cache_directory
        self.files_directory = app.files_directory
        self.cookies_file_path = app.cookies_file_path
        self.proxies_file_path = app.proxies_file_path
        self.config_file_path = app.config_file_path

        self.load_config()

    @abstractmethod
    def run(self):
        pass

    def load_config(self):
        """
        Injects the config file attributes into the Tool class
        """
        try:
            f = open(self.config_file_path)
        except FileNotFoundError:
            raise Exception("\033[1;31mConfig file not found. Make sure to have it in files/config.json\033[0;0m")
        
        data = f.read()
        f.close()
        x = json.loads(data)
        # inject specific tool config
        try:
            props = x[(self.name).replace(" ", "")]
            for prop in props:
                self.__dict__["config"][prop] = props[prop]
        except KeyError:
            # ignore if tool has no config
            pass
        # inject captcha tokens
        props = x["FunCaptchaSolvers"]
        for prop in props:
            self.__dict__["captcha_tokens"][prop.replace("_token", "")] = props[prop]
    
    def get_random_user_agent(self) -> str:
        """
        Generates a random user agent
        """
        ua = UserAgent(use_external_data=True)
        return ua.random

    def get_csrf_token(self, proxies:dict = None, cookie:str = None) -> str:
        """
        Retrieve a CSRF token from Roblox
        """

        headers = {'Cookie': ".ROBLOSECURITY=" + cookie } if cookie else None

        response = httpx.post("https://auth.roblox.com/v2/logout", headers=headers, proxies=proxies)

        csrf_token = response.headers.get("x-csrf-token")

        if csrf_token == None:
            raise Exception("CSRF TOKEN not found. Invalid cookie probably")
        
        return csrf_token
    
    def get_user_info(self, cookie, proxies, user_agent):
        req_url = "https://www.roblox.com/mobileapi/userinfo"
        req_cookies = { ".ROBLOSECURITY": cookie }
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        
        response = httpx.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)
        result = response.json()

        return {
            "UserID": result["UserID"],
            "UserName": result["UserName"],
            "RobuxBalance": result["RobuxBalance"],
            "ThumbnailUrl": result["ThumbnailUrl"],
            "IsAnyBuildersClubMember": result["IsAnyBuildersClubMember"],
            "IsPremium": result["IsPremium"]
        }
    
    def clear_line(self, line: str) -> str:
        return line.replace("\n", "").replace(" ", "").replace("\t", "")

    def get_cookies(self, amount = None) -> list:
        f = open(self.cookies_file_path, 'r+')
        cookies = f.read().splitlines()
        f.close()

        # ignore duplicates
        cookies = [*set(cookies)]
        random.shuffle(cookies)

        if amount is not None and amount < len(cookies):
            cookies = cookies[:self.max_generations]

        return cookies

    def print_status(self, req_worked, req_failed, total_req, response_text, has_worked, action_verb):
        print(f"\033[1A\033[K\033[1A\033[K\033[1;32m{action_verb}: {str(req_worked)}\033[0;0m | \033[1;31mFailed: {str(req_failed)}\033[0;0m | \033[1;34mTotal: {str(total_req)}\033[0;0m")
        print(f"\033[1;32mWorked: {response_text}\033[0;0m" if has_worked else f"\033[1;31mFailed: {response_text}\033[0;0m")

    def __str__(self) -> str:
        return "A Versatools tool. " + self.description