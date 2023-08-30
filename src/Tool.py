import os
import json
import random
import ipaddress
import requests
from abc import ABC, abstractmethod
from fake_useragent import UserAgent

class Tool(ABC):
    def __init__(self, name: str, description: str, color: int, app: object):
        self.color = color
        self.name = name
        self.description = description
        self.app = app
        self.cache_directory = app.cache_directory
        self.files_directory = app.files_directory
        self.supported_proxy_protocols = ["http", "socks4", "socks5"]

        self.config = {}
        self.captcha_tokens = {}

        self.config_file_path = os.path.join(os.path.dirname(__file__), "../files/config.json")
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
        ua = UserAgent()
        return ua.random

    def get_csrf_token(self, proxies:dict = None, cookie:str = None) -> str:
        """
        Retrieve a CSRF token from Roblox
        """

        headers = {'Cookie': ".ROBLOSECURITY=" + cookie } if cookie else None

        response = requests.post("https://auth.roblox.com/v2/logout", headers=headers, proxies=proxies)

        csrf_token = response.headers.get("x-csrf-token")
        return csrf_token
    
    def get_user_info(self, cookie, proxies, user_agent):
        req_url = "https://www.roblox.com/mobileapi/userinfo"
        req_cookies = { ".ROBLOSECURITY": cookie }
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        
        response = requests.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)
        result = response.json()

        return result["UserID"], result["UserName"], result["RobuxBalance"], result["ThumbnailUrl"], result["IsAnyBuildersClubMember"], result["IsPremium"]
    
    def clear_line(self, line: str) -> str:
        return line.replace("\n", "").replace(" ", "").replace("\t", "")

    # =======================
    # ==== PROXY METHODS ====
    # =======================
    def check_proxies_file_format(self, file_path: str, is_proxy_type_needed: bool) -> bool:
        """
        Checks proxies file format is good before checking/using proxies
        """
        try:
            f = open(file_path)
        except FileNotFoundError:
            raise FileNotFoundError("Please add your proxies in files/proxies.txt and try again")
        
        lines = f.readlines()
        f.close()
        
        for i, line in enumerate(lines):
            line = self.clear_line(line)
            line_number = i + 1

            # make sure no line is empty
            if (line == ""):
                raise SyntaxError("Please remove the empty line", (
                    file_path,
                    line_number,
                    None,
                    line
                ))
            
            try:
                proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(line)
            except ValueError as e:
                raise SyntaxError(e, (
                    file_path,
                    line_number,
                    None,
                    line
                ))
            
            # if proxy_type is needed, make sure it is provided
            if (is_proxy_type_needed and (proxy_type_provided != True)):
                raise SyntaxError("Proxy type is not provided", (
                    file_path,
                    line_number,
                    None,
                    line
                ))
            
            # make sure proxy_type is supported
            if (proxy_type_provided and proxy_type not in self.supported_proxy_protocols):
                raise SyntaxError("Proxy type not supported", (
                    file_path,
                    line_number,
                    None,
                    line
                ))            
            
            # validate proxy_port
            if not (0 <= proxy_port and proxy_port <= 65536):
                raise SyntaxError("Proxy port must be between 0 and 65536", (
                    file_path,
                    line_number,
                    None,
                    line
                ))   
        
        # if 0 proxy found, display error message
        if len(lines) == 0:
            raise Exception("\033[1;31mNo proxy found in files/proxies.txt. Please add some and try again\033[0;0m")

        return True
    
    def get_proxy_values(self, line: str) -> tuple:
        """
        Gets all proxy values from a line according to different line formats
        """
        num_item = len(line.split(":"))

        proxy_type = None
        proxy_user = None
        proxy_pass = None

        # get proxy_type (if provided), proxy_ip, proxy_port, proxy_user (if provided), proxy_pass (if provided)
        if (num_item in [2, 4]):
            proxy_type_provided = False
            proxy_ip = line.split(":")[0]
            proxy_port = line.split(":")[1]
            if (num_item == 4):
                proxy_user = line.split(":")[2]
                proxy_pass = line.split(":")[3]
        elif (num_item in [3, 5]):
            proxy_type_provided = True
            proxy_type = line.split(":")[0].lower()
            proxy_ip = line.split(":")[1]
            proxy_port = line.split(":")[2]
            if (num_item == 5):
                proxy_user = line.split(":")[3]
                proxy_pass = line.split(":")[4]
        else:
            raise ValueError("Incorrect proxy line format")
        
        try:
            proxy_port = int(proxy_port)
        except:
            raise ValueError("Proxy port must be a number")
        
        return proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass
    
    def get_proxies(self, proxy_type: str, proxy_ip: str, proxy_port: int, proxy_user: str = None, proxy_pass: str = None) -> dict:
        """
        Returns a dict of proxies
        """
        if (proxy_user is not None and proxy_pass is not None):
            auth = True
        elif (proxy_user is None and proxy_pass is None):
            auth = False
        else: 
            raise ValueError("Invalid Parameters. If proxy has auth, make sure to provide username and password")

        if auth:
            proxies = {
                "http": f"{proxy_type}://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}/",
                "https": f"{proxy_type}://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}/"
            }
        else:
            proxies = {
                "http": f"{proxy_type}://{proxy_ip}:{proxy_port}/",
                "https": f"{proxy_type}://{proxy_ip}:{proxy_port}/"
            }
        
        return proxies
    
    def get_random_proxies(self) -> dict:
        """
        Gets random proxies dict from proxies.txt file for requests module
        """

        # make sure proxies list is correctly formatted
        self.check_proxies_file_format(self.app.proxies_file_path, True)

        f = open(self.app.proxies_file_path, 'r')
        proxies_list = f.readlines()

        # get random line
        random_line = proxies_list[random.randint(0, len(proxies_list) - 1)]
        random_line = self.clear_line(random_line)
        # get proxies dict for requests module
        proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(random_line)
        proxies = self.get_proxies(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)
        
        return proxies

    def __str__(self) -> str:
        return "A Versatools tool. " + self.description