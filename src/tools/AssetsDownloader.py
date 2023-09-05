import os
from Tool import Tool
import concurrent.futures
from utils import Utils
import httpx

class AssetsDownloader(Tool):
    def __init__(self, app):
        super().__init__("Assets Downloader", "Download most trending assets from Roblox catalog", 1, app)

        self.max_generations = self.config["max_generations"]
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

        self.assets_files_directory = os.path.join(self.files_directory, "./assets")
        self.shirts_files_directory = os.path.join(self.files_directory, "./assets/shirts")
        self.pants_files_directory = os.path.join(self.files_directory, "./assets/pants")

        Utils.ensure_directories_exist([self.assets_files_directory, self.shirts_files_directory, self.pants_files_directory])

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

        try:
            assets = self.get_assets_amount("ClassicShirts" if choice == 1 else "ClassicPants", self.max_generations)
        except Exception as e:
            print(f"\033[1;31m{str(e)}\033[0;0m")
            return

        directory = self.shirts_files_directory if choice == 1 else self.pants_files_directory

        req_worked = 0
        req_failed = 0
        total_req = len(assets)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.download_asset, asset, directory) for asset in assets]

            for future in concurrent.futures.as_completed(results):
                try:
                    has_downloaded, response_text = future.result()
                except Exception as e:
                    has_downloaded, response_text = False, str(e)

                if has_downloaded:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, has_downloaded, "Downloaded")

    @Utils.retry_on_exception()
    def get_assets_page(self, asset_name, cursor):
        proxies = self.get_random_proxies() if self.use_proxy else None
        user_agent = self.get_random_user_agent()

        req_url = f"https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&minPrice=5&salesTypeFilter=1&sortAggregation=1&sortType=2&subcategory={asset_name}{'&cursor='+cursor if cursor else ''}"
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        
        response = httpx.get(req_url, headers=req_headers, proxies=proxies)
        result = response.json()
        data = result["data"]
        cursor = result["nextPageCursor"]

        return data, cursor

    def get_assets_amount(self, asset_name, amount):
        """
        Get x amount of assets
        """
        assets = []
        cursor = None

        while (len(assets) < amount):
            data, cursor = self.get_assets_page(asset_name, cursor)
        
            assets += data
        
        assets = assets[:amount]
        return assets

    @Utils.retry_on_exception()
    def download_asset(self, asset, directory):
        asset_id = asset["id"]
        proxies = self.get_random_proxies() if self.use_proxy else None

        with httpx.Client(proxies=proxies) as client:
            assetdelivery = client.get(f'https://assetdelivery.roblox.com/v1/assetId/{asset_id}').json()['location']
            assetid = str(client.get(assetdelivery).content).split('<url>http://www.roblox.com/asset/?id=')[1].split('</url>')[0]
            png = client.get(f'https://assetdelivery.roblox.com/v1/assetId/{assetid}').json()['location']
            image = client.get(png).content
            asset_path = os.path.join(directory, f"{asset_id}.png")

        with open(asset_path, 'wb') as f:
            f.write(image)
        
        return True, "Generated in files/assets"