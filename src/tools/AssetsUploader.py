import os
import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils
import requests
import time

class AssetsUploader(Tool):
    def __init__(self, app):
        super().__init__("Assets Uploader", "Integrates with AssetsDownloader to upload clothing", 8, app)

        self.assets_files_directory = os.path.join(self.files_directory, "./assets")
        self.shirts_files_directory = os.path.join(self.files_directory, "./assets/shirts")
        self.pants_files_directory = os.path.join(self.files_directory, "./assets/pants")

        Utils.ensure_directories_exist([self.assets_files_directory, self.shirts_files_directory, self.pants_files_directory])

    def run(self):
        shirts = os.listdir(self.shirts_files_directory)
        pants = os.listdir(self.pants_files_directory)
        assets = [{"file": shirt, "type": "shirt"} for shirt in shirts] + [{"file": pant, "type": "pant"} for pant in pants]

        if len(assets) == 0:
            raise Exception("No assets found. Make sure to download some first")

        req_worked = 0
        req_failed = 0
        total_req = len(assets)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.upload_asset, asset) for asset in assets]

            for future in concurrent.futures.as_completed(results):
                try:
                    has_uploaded, response_text = future.result()
                except Exception as err:
                    has_uploaded, response_text = False, str(err)
            
                if has_uploaded:
                    req_worked += 1
                else:
                    req_failed += 1
            
                self.print_status(req_worked, req_failed, total_req, response_text, has_uploaded, "Uploaded")

    def upload_asset(self, asset):
        time.sleep(self.config["timeout"])

        asset_file = asset["file"]
        asset_id = asset_file.replace(".png", "")
        asset_name = self.get_asset_name(asset_id)
        asset_type = asset["type"]
        asset_path = os.path.join(self.assets_files_directory, f"./{asset_type}s/{asset_file}")

        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, self.config["cookie"])

        req_json = {
            "displayName": asset_name,
            "description": self.config["description"],
            "assetType": "Shirt" if asset_type == "shirt" else "Pants",
            "creationContext":{
                "creator": {
                    "groupId": self.config["group_id"]
                },
                "expectedPrice": 10
            }
        }
        
        req_url = "https://apis.roblox.com/assets/user-auth/v1/assets"
        req_cookies = { ".ROBLOSECURITY": self.config["cookie"] }
        
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_headers["Content-Type"] = None

        with open(asset_path, "rb") as f:
            image_file = f.read()

        files = {
            "fileContent": ("robloxasset.png", image_file, "image/png"),
            "request": (None, str(req_json))
        }

        result = requests.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, files=files)
        response = result.json()
        if (result.status_code != 200):
            return False, result.text
        
        operationId = response["operationId"]
        done = response["done"]

        # delete the img file
        os.remove(asset_path)

        while (done is not True):
            done, response = self.get_asset_id(operationId)
            if (done is True):
                asset_id = response["assetId"]

        return self.publish_asset(asset_id)

    @Utils.retry_on_exception()
    def publish_asset(self, asset_id):
        req_url = f"https://itemconfiguration.roblox.com/v1/assets/{asset_id}/release"
        req_cookies = {".ROBLOSECURITY": self.config["cookie"]}
        req_json={"priceConfiguration": {"priceInRobux": self.config["robux_price"]}, "releaseConfiguration": {"saleAvailabilityLocations": [0, 1]}, "saleStatus": "OnSale"}
        
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, self.config["cookie"])
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        
        req = requests.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)

        return True, req.text

    @Utils.retry_on_exception()
    def get_asset_id(self, operationId):
        req_url = f"https://apis.roblox.com/assets/user-auth/v1/operations/{operationId}"
        req_cookies = { ".ROBLOSECURITY": self.config["cookie"] }
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        req_headers = self.get_roblox_headers(user_agent)

        result = requests.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)
        response = result.json()
        done = response["done"]
        response = response.get("response") if done else False

        return done, response

    @Utils.retry_on_exception()
    def get_asset_name(self, asset_id):
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, self.config["cookie"])

        req_url = "https://catalog.roblox.com/v1/catalog/items/details"
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_json = {
          "items": [
            {
              "itemType": "Asset",
              "id": asset_id,
              "key":f"Asset_{asset_id}",
              "thumbnailType":"Asset"
            }
          ]
        }
        req_cookies = { ".ROBLOSECURITY": self.config["cookie"]}

        result = httpx.post(req_url, headers=req_headers, json=req_json, cookies=req_cookies, proxies=proxies)
        response = result.json()
        asset_name = response["data"][0]['name']

        return asset_name