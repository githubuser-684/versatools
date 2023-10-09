import os
import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils
import random
from PIL import Image

class AssetsDownloader(Tool):
    def __init__(self, app):
        super().__init__("Assets Downloader", "Download most trending assets from Roblox catalog", 1, app)

        self.assets_files_directory = os.path.join(self.files_directory, "./assets")
        self.shirts_files_directory = os.path.join(self.files_directory, "./assets/shirts")
        self.pants_files_directory = os.path.join(self.files_directory, "./assets/pants")

        self.cache_template_path = os.path.join(self.cache_directory, "asset-template.png")

        Utils.ensure_directories_exist([self.assets_files_directory, self.shirts_files_directory, self.pants_files_directory])

    def run(self):
        if self.config["sort"] not in self.config["//sorts"]:
            raise Exception(f"Invalid sort config key \"{self.config['sort']}\"")

        if self.config["asset_type"] not in ["shirt", "pants"]:
            raise Exception("Invalid asset type. Must be either \"shirt\" or \"pants\"")

        assets = self.get_assets_amount(self.config["max_generations"])

        req_worked = 0
        req_failed = 0
        total_req = len(assets)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.download_asset, asset) for asset in assets]

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

        salesTypeFilter = None
        sortAggregation = None
        sortType = None

        if self.config["sort"] == "relevance":
            salesTypeFilter = 1
        elif self.config["sort"] == "favouritedalltime":
            salesTypeFilter = 1
            sortAggregation = 5
            sortType = 1
        elif self.config["sort"] == "favouritedallweek":
            salesTypeFilter = 1
            sortAggregation = 3
            sortType = 1
        elif self.config["sort"] == "favouritedallday":
            salesTypeFilter = 1
            sortAggregation = 1
            sortType = 1
        elif self.config["sort"] == "bestsellingalltime":
            salesTypeFilter = 1
            sortAggregation = 5
            sortType = 2
        elif self.config["sort"] == "bestsellingweek":
            salesTypeFilter = 1
            sortAggregation = 3
            sortType = 2
        elif self.config["sort"] == "bestsellingday":
            salesTypeFilter = 1
            sortAggregation = 1
            sortType = 2
        elif self.config["sort"] == "recentlycreated":
            salesTypeFilter = 1
            sortType = 3
        elif self.config["sort"] == "pricehightolow":
            salesTypeFilter = 1
            sortType = 5
        elif self.config["sort"] == "pricelowtohigh":
            salesTypeFilter = 1
            sortType = 4

        req_url = f"https://catalog.roblox.com/v1/search/items"
        req_headers = self.get_roblox_headers(user_agent)
        req_params = {
            "category": "Clothing",
            "limit": 120,
            "minPrice": 5,
            "salesTypeFilter": salesTypeFilter,
            "sortAggregation": sortAggregation,
            "sortType": sortType,
            "subcategory": asset_name,
            "cursor": cursor,
            "keyword": self.config["keyword"]
        }

        response = httpx.get(req_url, headers=req_headers, params=req_params, proxies=proxies)
        result = response.json()
        data = result["data"]
        cursor = result["nextPageCursor"]

        return data, cursor

    def get_assets_amount(self,  amount):
        """
        Get x amount of assets
        """
        assets = []
        cursor = None

        while len(assets) < amount:
            data, cursor = self.get_assets_page("ClassicShirts" if self.config["asset_type"] == "shirt" else "ClassicPants", cursor)

            if self.config["asset_type"] == "shirt":
                for asset in data:
                    asset["shirt"] = True

            assets += data
            random.shuffle(assets)

        assets = assets[:amount]
        return assets

    @Utils.retry_on_exception()
    def download_asset(self, asset):
        """
        Download an asset
        """
        # get directory
        directory = self.shirts_files_directory if asset.get("shirt") else self.pants_files_directory

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

        if self.config["remove_trademark"]:
            self.remove_trademark(asset_path)

        return True, "Generated in files/assets"

    def remove_trademark(self, asset_path):
        self.ensure_template_exists()

        trademarked_img = Image.open(asset_path)
        template = Image.open(self.cache_template_path)

        trademarked_img.paste(template, (0,0), mask = template)
        trademarked_img.save(asset_path)

    def ensure_template_exists(self):
        if not os.path.exists(self.cache_template_path):
            with open(self.cache_template_path, 'wb') as f:
                png = httpx.get(f'https://rofuel.com/wp-content/uploads/2023/10/shirt.png').content
                f.write(png)
