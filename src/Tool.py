import json
import random
import httpx
from abc import ABC, abstractmethod
from Proxy import Proxy
from fake_useragent import UserAgent
from utils import Utils
import eel

class Tool(Proxy, ABC):
    def __init__(self, name: str, description: str, color: int, app: object):
        super().__init__()

        self.color = color
        self.name = name
        self.description = description
        self.app = app
        self.executor = None

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
        """
        Runs the tool
        """

    def load_config(self):
        """
        Injects the config file attributes into the Tool class
        """
        try:
            f = open(self.config_file_path)
        except FileNotFoundError:
            raise Exception("\x1B[1;31mConfig file not found. Make sure to have it in files/config.json\x1B[0;0m")

        data = f.read()
        f.close()
        x = json.loads(data)
        # inject specific tool config
        try:
            props = x[(self.name).replace(" ", "")]
            for prop in props:
                self.config[prop] = props[prop]
        except KeyError:
            # ignore if tool has no config
            pass
        # inject captcha tokens
        props = x["FunCaptchaSolvers"]
        for prop in props:
            self.captcha_tokens[prop.replace("_token", "")] = props[prop]

        return self.config

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

        if csrf_token is None:
            raise Exception("CSRF TOKEN not found. Invalid cookie probably")

        return csrf_token

    def get_user_info(self, cookie, proxies, user_agent):
        """
        Gets the user info from the Roblox API
        """
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

    def get_cookies(self, amount = None) -> list:
        """
        Gets cookies from cookies.txt file
        """
        f = open(self.cookies_file_path, 'r+')
        cookies = f.read().splitlines()
        f.close()

        # ignore duplicates
        cookies = [*set(cookies)]
        random.shuffle(cookies)

        if len(cookies) == 0:
            raise Exception("No cookies found. Make sure to generate some first")

        if amount is not None and amount < len(cookies):
            cookies = cookies[:amount]

        return cookies

    def get_random_proxies(self) -> dict:
        """
        Gets random proxies dict from proxies.txt file for httpx module
        """
        try:
            f = open(self.app.proxies_file_path, 'r')
        except FileNotFoundError:
            raise FileNotFoundError("files/proxies.txt path not found. Create it, add proxies and try again")

        proxies_list = f.readlines()
        proxies_list = [*set(proxies_list)] # remove duplicates

        if len(proxies_list) == 0:
            raise Exception("No proxies found in files/proxies.txt. Please add some and try again")

        # get random line
        random_line = proxies_list[random.randint(0, len(proxies_list) - 1)]
        random_line = Utils.clear_line(random_line)
        # get proxies dict for httpx module
        proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(random_line)
        proxies = self.get_proxies(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)

        return proxies

    def print_status(self, req_worked, req_failed, total_req, response_text, has_worked, action_verb):
        """
        Prints the status of a request
        """
        eel.set_stats(f"{action_verb}: {str(req_worked)} | Failed: {str(req_failed)} | Total: {str(total_req)}")
        eel.write_terminal(f"\x1B[1;32mWorked: {response_text}\x1B[0;0m" if has_worked else f"\x1B[1;31mFailed: {response_text}\x1B[0;0m")

    # pylint: disable = unused-argument
    def signal_handler(self):
        """
        Handles the signal
        """
        if self.executor is not None:
            self.executor.shutdown(wait=True, cancel_futures=True)

    def __str__(self) -> str:
        return "A Versatools tool. " + self.description
