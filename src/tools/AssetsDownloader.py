import os
import requests
import time
from Tool import Tool
import concurrent.futures

class AssetsDownloader(Tool):
    def __init__(self, app):
        super().__init__("Assets Downloader", "Download most trending assets from Roblox catalog", 1, app)

        self.max_generations = self.config["max_generations"]
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

        self.assets_files_directory = os.path.join(self.files_directory, "./assets")

        # ensure assets dir exists
        if not os.path.exists(self.assets_files_directory):
            os.makedirs(self.assets_files_directory)

        self.shirts_files_directory = os.path.join(self.files_directory, "./assets/shirts")
        self.pants_files_directory = os.path.join(self.files_directory, "./assets/pants")

        # ensure shirts/pants dir exists
        if not os.path.exists(self.shirts_files_directory):
            os.makedirs(self.shirts_files_directory)
        if not os.path.exists(self.pants_files_directory):
            os.makedirs(self.pants_files_directory)

    def run(self):
        print("1. Download shirts")
        print("2. Download pants")
        
        askAgain = True
        while askAgain:
            choice = input("\033[0;0mEnter your choice: ")

            if (choice.isnumeric() and int(choice) > 0 and int(choice) < 3):
                choice = int(choice)
                askAgain = False

            if askAgain:
                print("\033[0;33mInvalid choice\033[0;0m")

        if (choice == 1):
            assets = self.get_assets("ClassicShirts", self.max_generations)
            directory = self.shirts_files_directory

        if (choice == 2):
            assets = self.get_assets("ClassicPants", self.max_generations)
            directory = self.pants_files_directory
        
        req_worked = 0
        req_failed = 0
        total_req = len(assets)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.download_asset, asset, directory) for asset in assets]

            for future in concurrent.futures.as_completed(results):
                has_downloaded, response_text = future.result()

                if has_downloaded:
                    req_worked += 1
                else:
                    req_failed += 1

                print("\033[1A\033[K\033[1A\033[K\033[1;32mDownloaded: "+str(req_worked)+"\033[0;0m | \033[1;31mFailed: "+str(req_failed)+"\033[0;0m | \033[1;34mTotal: "+str(total_req) + "\033[0;0m")
                print("\033[1;32mWorked: " + response_text + "\033[0;0m" if has_downloaded else "\033[1;31mFailed: " + response_text + "\033[0;0m")

    def get_assets(self, asset_name, amount):
        assets = []
        cursor = None

        while (len(assets) < amount):
            proxies = self.get_random_proxies() if self.use_proxy else None
            csrf_token = self.get_csrf_token(proxies)
            user_agent = self.get_random_user_agent()

            req_url = f"https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&minPrice=5&salesTypeFilter=1&sortAggregation=1&sortType=2&subcategory={asset_name}{'&cursor='+cursor if cursor else ''}"
            req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

            for _ in range(3):
                try:
                    response = requests.get(req_url, headers=req_headers, proxies=proxies)
                    result = response.json()
                    data = result["data"]
                    cursor = result["nextPageCursor"]
                    break
                except:
                    time.sleep(2)
            else:
                raise Exception("Error fetching assets. too many tries")
        
            assets += data
        
        assets = assets[:amount]
        return assets
    
    def download_asset(self, asset, directory):
        asset_id = asset["id"]
        proxies = self.get_random_proxies() if self.use_proxy else None

        try:
            assetdelivery = requests.get(f'https://assetdelivery.roblox.com/v1/assetId/{asset_id}', proxies=proxies).json()['location']
            assetid = str(requests.get(assetdelivery, proxies=proxies).content).split('<url>http://www.roblox.com/asset/?id=')[1].split('</url>')[0]
            png = requests.get(f'https://assetdelivery.roblox.com/v1/assetId/{assetid}', proxies=proxies).json()['location']
            image = requests.get(png, proxies=proxies).content
            asset_path = os.path.join(directory, f"{asset_id}.png")
        except Exception as e:
            return False, str(e)
        
        with open(asset_path, 'wb') as f:
            f.write(image)
        
        return True, "lol"