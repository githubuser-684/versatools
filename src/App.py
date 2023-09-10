import os
from tools import ProxyChecker,CookieGenerator,CookieRefresher,CookieChecker,CookieVerifier,TShirtGenerator,MessageBot,FriendRequestBot,StatusChanger,FollowBot,GameVote,FavoriteBot,DisplayNameChanger,SolverBalanceChecker,GroupJoinBot,AssetsDownloader,CommentBot,Gen2018Acc
from Tool import Tool
from utils import Utils
import json
from data.config import config

class App():
    def __init__(self):
        self.cache_directory = os.path.join(os.path.dirname(__file__), "../.versacache")
        self.files_directory = os.path.join(os.path.dirname(__file__), "../files")
        self.proxies_file_path = os.path.join(self.files_directory, "proxies.txt")
        self.cookies_file_path = os.path.join(self.files_directory, "cookies.txt")
        self.config_file_path = os.path.join(self.files_directory, "config.json")

        Utils.ensure_directories_exist([self.cache_directory, self.files_directory])
        Utils.ensure_files_exist([self.proxies_file_path, self.cookies_file_path])
        self.ensure_config_file_exists()

    def clear_terminal(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_logo(self) -> str:
        return """
        _  _ ____ ____ ____ ____ ___ ____ ____ _    ____ 
        |  | |___ |__/ [__  |__|  |  |  | |  | |    [__  
         \/  |___ |  \ ___] |  |  |  |__| |__| |___ ___] 
        """

    def run(self):
        """
        Runs the app
        """
        self.clear_terminal()

        print(self.get_logo())
        print("\033[1;32mWelcome to Versatools")
        print("\033[0;0mBest FREE opensource Roblox botting tools written in Python\n")
        print("\033[1;31mOur tools:")

        tools = self.get_tools_list()

        for i, tool in enumerate(tools):
            print(f"\033[1;3{tool.color}m   {str(i + 1)}. {tool.name}")
            print(f"      {tool.description}")

        askAgain = True
        while askAgain:
            choice = input("\033[0;0mEnter your choice: ")
    
            for i, tool in enumerate(tools):
                if (choice.isnumeric() and i + 1 == int(choice)):
                    self.launch_tool(tool)
                    lastToolExecuted = tool
                    askAgain = False
            if askAgain:
                print("\033[0;33mInvalid choice\033[0;0m")

        while True:
            choice = input("\n\033[0;32m1. Run Again\n2. Go to menu\033[0;0m\n")
            if (not choice.isnumeric()):
                print("\033[0;33mPlease enter a number\033[0;0m")
            elif (int(choice) == 1):
                self.launch_tool(lastToolExecuted)
            elif (int(choice) == 2):
                self.run()
            else:
                print("\033[0;33mInvalid choice\033[0;0m")
    
    def launch_tool(self, tool):
        tool.load_config()
        tool.setup_signal()

        try:
            tool.run()
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(f"\033[1;31m{str(e)}\033[0;0m")
            return

    def get_tools_list(self):
        """
        Returns a list of all instances of tools
        """
        tools = [t(self) for t in Tool.__subclasses__()]
        sorted_tools = sorted(tools, key=lambda x: x.name)
        return sorted_tools
    
    def ensure_config_file_exists(self):
        """
        Ensure config file exists.
        If doesn't exist, create it with default config
        """
        config_file_path = os.path.join(self.files_directory, "config.json")
        if (not os.path.exists(config_file_path)):
            with open(config_file_path, "w") as json_file:
                json.dump(config, json_file, indent=4)

    def __str__(self) -> str:
        return "Versatools main class"