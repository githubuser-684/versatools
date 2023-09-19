import os
import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils
import eel

class AssetsDownloader(Tool):
    def __init__(self, app):
        super().__init__("Assets Downloader", "Download most trending assets from Roblox catalog", 1, app)

        self.assets_files_directory = os.path.join(self.files_directory, "./assets")
        self.shirts_files_directory = os.path.join(self.files_directory, "./assets/shirts")
        self.pants_files_directory = os.path.join(self.files_directory, "./assets/pants")

        Utils.ensure_directories_exist([self.assets_files_directory, self.shirts_files_directory, self.pants_files_directory])

    def run(self):
        eel.write_terminal("1. Download shirts")
        eel.write_terminal("2. Download pants")

        ask_again = True
        while ask_again:
            choice = eel.input("\x1B[0;0mEnter your choice: ")()
            print(choice)

            if (choice.isnumeric() and int(choice) > 0 and int(choice) < 3):
                choice = int(choice)
                ask_again = False

            if ask_again:
                eel.write_terminal("\x1B[0;33mInvalid choice\x1B[0;0m")

        assets = self.get_assets_amount("ClassicShirts" if choice == 1 else "ClassicPants", self.config["max_generations"])
        directory = self.shirts_files_directory if choice == 1 else self.pants_files_directory

        req_worked = 0
        req_failed = 0
        total_req = len(assets)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.download_asset, asset, directory) for asset in assets]

            for future in concurrent.futures.as_completed(results):
                try:
                    has_downloaded, response_text = future.result()
                except Exception as err:
                    has_downloaded, response_text = False, str(err)

                if has_downloaded:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, has_downloaded, "Downloaded")

    @Utils.retry_on_exception()
    def get_assets_page(self, asset_name, cursor):
        """
        Get a page of assets
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()

        req_url = f"https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&minPrice=5&salesTypeFilter=1&sortAggregation=1&sortType=2&subcategory={asset_name}{'&cursor='+cursor if cursor else ''}"
        req_headers = self.get_roblox_headers(user_agent)

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

        while len(assets) < amount:
            data, cursor = self.get_assets_page(asset_name, cursor)

            assets += data

        assets = assets[:amount]
        return assets

    @Utils.retry_on_exception()
    def download_asset(self, asset, directory):
        """
        Download an asset
        """
        asset_id = asset["id"]
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None

        with httpx.Client(proxies=proxies) as client:
            assetdelivery = client.get(f'https://assetdelivery.roblox.com/v1/assetId/{asset_id}').json()['location']
            assetid = str(client.get(assetdelivery).content).split('<url>http://www.roblox.com/asset/?id=')[1].split('</url>')[0]
            png = client.get(f'https://assetdelivery.roblox.com/v1/assetId/{assetid}').json()['location']
            image = client.get(png).content
            asset_path = os.path.join(directory, f"{asset_id}.png")

        with open(asset_path, 'wb') as f:
            f.write(image)
            f.flush()

        return True, "Generated in files/assets"
