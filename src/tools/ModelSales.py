import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils

class ModelSales(Tool):
    def __init__(self, app):
        super().__init__("Model Sales", "Buy your Roblox models tons of times", 3, app)

        self.config["max_generations"] 
        self.config["max_workers"]
        self.config["use_proxy"]

    def run(self):
        asset_id = input("Asset ID to buy: ")
        
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        product_id = self.get_product_id(asset_id, cookies[0])

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.buy_product, asset_id, product_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    response_text = future.result()
                    is_success = True
                    req_sent += 1
                except Exception as e:
                    response_text = str(e)
                    is_success = False
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "Bought")

    def get_product_id(self, asset_id, cookie):
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()

        req_url = f"https://apis.roblox.com/toolbox-service/v1/items/details?assetIds={asset_id}"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent)

        response = httpx.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)

        try:
            product_id = response.json()["data"][0]["product"]["productId"]
        except:
            raise Exception(response.text + " Status code: " + str(response.status_code))
        
        return product_id

    @Utils.retry_on_exception()
    def buy_product(self, asset_id, product_id, cookie):
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        req_url = f"https://apis.roblox.com/creator-marketplace-purchasing-service/v1/products/{product_id}/purchase"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_json = {"assetId": asset_id, "assetType": 10, "expectedPrice": 0, "searchId": ""}

        response = httpx.post(req_url, headers=req_headers, json=req_json, cookies=req_cookies, proxies=proxies)

        if (response.status_code != 200):
            raise Exception(response.text)
        
        return response.text