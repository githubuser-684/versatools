import os
from tools import ProxyChecker,CookieGenerator,CookieRefresher,CookieChecker,CookieVerifier,TShirtGenerator,MessageBot,FriendRequestBot,StatusChanger,GameVote,FavoriteBot,DisplayNameChanger,SolverBalanceChecker,GroupJoinBot,AssetsDownloader,CommentBot,Gen2018Acc,ModelSales,AssetsUploader,ModelVote,AdsScraper,ProxyScraper,GameVisits,DiscordRpc,ItemBuyer,ReportBot,UP2UPC,VipServerScraper,GroupAllyBot,DiscordNitroGen,UsernameSniper,PasswordChanger,CookieRegionUnlocker
from Tool import Tool
from utils import Utils
import json
from data.config import config
from data.version import version

class App():
    def __init__(self):
        self.cache_directory = os.path.join(os.path.dirname(__file__), "../.versacache")
        self.files_directory = os.path.join(os.path.dirname(__file__), "../files")
        self.proxies_file_path = os.path.join(self.files_directory, "proxies.txt")
        self.cookies_file_path = os.path.join(self.files_directory, "cookies.txt")
        self.config_file_path = os.path.join(self.files_directory, "config.json")

        self.current_tool = None
        self.selected_tool = None
        self.proxies_loaded = None
        self.cookies_loaded = None

        Utils.ensure_directories_exist([self.cache_directory, self.files_directory])
        Utils.ensure_files_exist([self.proxies_file_path, self.cookies_file_path])

        self.ensure_config_file()
        self.tools = [t(self) for t in Tool.__subclasses__()]

    @staticmethod
    def get_version():
        return version

    def launch_tool(self, tool):
        tool.run()

    def get_tool_from(self, tool_identifier):
        """
        Returns the tool from its name or number
        """
        if tool_identifier.isdigit():
            tool_name = self.tools[int(tool_identifier) - 1].name
        else:
            # match the closest tool name
            tool_name = Utils.get_closest_match(tool_identifier, [tool.name for tool in self.tools])

        if tool_name is None:
            raise Exception("Tool not found")

        return self.get_tool_from_name(tool_name)

    def get_tool_from_name(self, tool_name):
        """
        Returns the tool from its name
        """
        tool = next((t for t in self.tools if t.name == tool_name), None)
        return tool

    def ensure_config_file(self):
        """
        Ensure config file exists and is valid
        """
        config_file_path = os.path.join(self.files_directory, "config.json")
        # make sure config file exists
        if not os.path.exists(config_file_path):
            with open(config_file_path, "w") as json_file:
                json.dump(config, json_file, indent=4)
        else:
            # make sure config file contains all keys and not more
            with open(config_file_path, "r+") as json_file:
                file_config = json.load(json_file)
                for key in config:
                    if key not in file_config:
                        file_config[key] = config[key]
                    else:
                        for subkey in config[key]:
                            if subkey not in file_config[key]:
                                file_config[key][subkey] = config[key][subkey]

                            # make sure subkeys starting with // are not overwritten
                            if subkey.startswith("//"):
                                file_config[key][subkey] = config[key][subkey]

                # make sure there are no extra keys
                for key in list(file_config):
                    if key not in config:
                        del file_config[key]
                    else:
                        for subkey in list(file_config[key]):
                            if subkey not in config[key]:
                                del file_config[key][subkey]

                json_file.seek(0)
                json_file.truncate()
                json.dump(file_config, json_file, indent=4)

    def update_config_prop(self, prop_name, config):
        with open(self.config_file_path, "r+") as json_file:
            file_config = json.load(json_file)
            file_config[prop_name.replace(" ", "")] = config
            json_file.seek(0)
            json_file.truncate()
            json.dump(file_config, json_file, indent=4)

    def set_solver_config(self, config):
        self.update_config_prop("FunCaptchaSolvers", config)

    def get_solver_config(self):
        try:
            f = open(self.config_file_path)
        except FileNotFoundError:
            raise Exception("\x1B[1;31mConfig file not found. Make sure to have it in files/config.json\x1B[0;0m")

        data = f.read()
        f.close()
        x = json.loads(data)

        return x["FunCaptchaSolvers"]

    def set_tool_config(self, tool, tool_config):
        tool.config = tool_config
        self.update_config_prop(tool.name, tool.config)

    def get_proxies_loaded(self):
        try:
            f = open(self.proxies_file_path, 'r')
        except FileNotFoundError:
            amount = 0

        proxies_list = f.readlines()
        f.close()
        proxies_list = [*set(proxies_list)] # remove duplicates
        amount = len(proxies_list)

        self.proxies_loaded = amount

        return amount

    def get_cookies_loaded(self):
        amount = len(self.tools[0].get_cookies(ignore_zero_cookie=True))

        if amount != self.cookies_loaded:
            self.cookies_loaded = amount

        return amount

    def start_files_dir(self):
        os.startfile(self.files_directory)

    def __str__(self) -> str:
        return "Versatools main class"
