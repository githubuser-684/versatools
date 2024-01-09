import json
import random
import httpc
from abc import ABC, abstractmethod
from Proxy import Proxy
from utils import Utils
import click
import re

class Tool(Proxy, ABC):
    def __init__(self, name: str, description: str,  app: object):
        super().__init__()

        self.name = name
        self.description = description
        self.app = app
        self.results = None
        self.exit_flag = False
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
        raise NotImplementedError("Domain Driven Design")

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

    def get_csrf_token(self, cookie:str, client = httpc) -> str:
        """
        Retrieve a CSRF token from Roblox
        """
        cookies = {'.ROBLOSECURITY':cookie } if cookie is not None else None
        response = client.post("https://auth.roblox.com/v2/login", cookies=cookies)

        try:
            csrf_token = response.headers["X-Csrf-Token"]
        except KeyError:
            raise Exception(Utils.return_res(response))

        return csrf_token

    def get_user_info(self, cookie, client, user_agent):
        """
        Gets the user info from the Roblox API
        """
        req_url = "https://www.roblox.com/mobileapi/userinfo"
        req_cookies = { ".ROBLOSECURITY": cookie }
        req_headers = httpc.get_roblox_headers(user_agent)

        response = client.get(req_url, headers=req_headers, cookies=req_cookies)
        if (response.status_code != 200):
            raise Exception(Utils.return_res(response))

        result = response.json()

        return {
            "UserID": result["UserID"],
            "UserName": result["UserName"],
            "RobuxBalance": result["RobuxBalance"],
            "ThumbnailUrl": result["ThumbnailUrl"],
            "IsAnyBuildersClubMember": result["IsAnyBuildersClubMember"],
            "IsPremium": result["IsPremium"]
        }

    def get_cookies(self, amount = None, provide_lines = False, **kwargs) -> list:
        """
        Gets cookies from cookies.txt file
        """
        f = open(self.cookies_file_path, 'r+')
        lines = f.read().splitlines()
        f.close()

        # ignore duplicates
        lines = [*set(lines)]
        random.shuffle(lines)

        # take only the cookie (not u:p)
        pattern = re.compile(r'_\|WARNING:-DO-NOT-SHARE-THIS\.-.*')
        cookies = [match.group(0) for line in lines for match in [pattern.search(line)] if match]

        if len(cookies) == 0 and kwargs.get("ignore_zero_cookie") != True:
            raise Exception("No cookies found. Make sure to generate some first")

        if amount is not None and amount < len(cookies):
            cookies = cookies[:amount]

        if provide_lines:
            return cookies, lines

        return cookies

    def get_random_cookie(self) -> str:
        return self.get_cookies(1)[0]

    def get_random_proxy(self) -> dict:
        """
        Gets random proxy dict
        """
        try:
            f = open(self.app.proxies_file_path, 'r')
        except FileNotFoundError:
            raise FileNotFoundError("files/proxies.txt path not found. Create it, add proxies and try again")

        proxies_list = f.readlines()
        f.close()
        proxies_list = [*set(proxies_list)] # remove duplicates

        if len(proxies_list) == 0:
            raise Exception("No proxies found in files/proxies.txt. Please add some and try again")

        # get random line
        random_line = proxies_list[random.randint(0, len(proxies_list) - 1)]
        random_line = Utils.clear_line(random_line)
        # get proxies dict for httpc module
        proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(random_line)
        proxy = self.get_proxies(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)

        return proxy

    def print_status(self, req_worked, req_failed, total_req, response_text, has_worked, action_verb):
        """
        Prints the status of a request
        """
        click.secho("\033[1A\033[K"+response_text, fg="red" if not has_worked else "green")

        output = ""
        output += click.style(f"{action_verb}: {str(req_worked)}", fg="green")
        output += " | "
        output += click.style(f"Failed: {str(req_failed)}", fg="red")
        output += " | "
        output += f"Total: {str(total_req)}"

        click.echo(output)

    def signal_handler(self):
        """
        Handles the signal
        """
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)

        self.exit_flag = True

    @staticmethod
    def run_until_exit(func):
        def wrapper(instance, *args, **kwargs):
            while True:
                result = func(instance, *args, **kwargs)

                if instance.exit_flag:
                    break
            return result
        return wrapper

    def __str__(self) -> str:
        return "A Versatools tool. " + self.description
