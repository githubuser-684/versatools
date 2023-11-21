import concurrent.futures
import httpc
from Tool import Tool
from utils import Utils

class ModelSales(Tool):
    def __init__(self, app):
        super().__init__("Model Sales", "Buy your Roblox models tons of times", 3, app)

    @Tool.handle_exit
    def run(self):
        asset_id = self.config["asset_id"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        product_id = self.get_product_id(asset_id, cookies[0])

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.buy_product, asset_id, product_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_bought, response_text = future.result()
                except Exception as e:
                    is_bought, response_text = False, str(e)

                if is_bought:
                    is_success = True
                    req_sent += 1
                else:
                    is_success = False
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "Bought")

    @Utils.handle_exception(2)
    def get_product_id(self, asset_id, cookie):
        """
        Get the product ID of an asset
        """
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None
        user_agent = httpc.get_random_user_agent()

        req_url = f"https://apis.roblox.com/toolbox-service/v1/items/details?assetIds={asset_id}"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = httpc.get_roblox_headers(user_agent)

        response = httpc.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)

        try:
            product_id = response.json()["data"][0]["product"]["productId"]
        except:
            raise Exception(Utils.return_res(response))

        return product_id

    @Utils.handle_exception(3)
    def buy_product(self, asset_id, product_id, cookie):
        """
        Buy a product
        """
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = f"https://apis.roblox.com/creator-marketplace-purchasing-service/v1/products/{product_id}/purchase"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
            req_json = {"assetId": asset_id, "assetType": 10, "expectedPrice": 0, "searchId": ""}

            response = client.post(req_url, headers=req_headers, json=req_json, cookies=req_cookies)

        try:
            is_bought = (response.status_code == 200 and response.json()["purchased"] is True)
        except Exception:
            raise Exception("Failed to access purchased key " + Utils.return_res(response))

        return is_bought, Utils.return_res(response)
