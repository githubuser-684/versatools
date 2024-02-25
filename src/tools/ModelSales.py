import concurrent.futures
import httpc
from Tool import Tool
from utils import Utils

class ModelSales(Tool):
    def __init__(self, app):
        super().__init__("Model Sales", "Buy your Roblox models tons of times", app)

    def run(self):
        asset_id = self.config["asset_id"]
        cookies = self.get_cookies(self.config["max_generations"])
        leave_review_when_bought = self.config["leave_review_when_bought"]
        review_message = self.config["review_message"]

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        product_id = self.get_product_id(asset_id, cookies[0])

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.buy_product, asset_id, product_id, leave_review_when_bought, review_message, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(self.results):
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
    def buy_product(self, asset_id, product_id, leave_review_when_bought, review_message, cookie):
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
            except KeyError:
                return False, "Failed to access purchased key " + Utils.return_res(response)

            if leave_review_when_bought:
                reviewed, response = self.leave_review(asset_id, cookie, review_message, user_agent, csrf_token, client)

                if not reviewed:
                    return False, "Failed to leave review " + Utils.return_res(response)

        return is_bought, Utils.return_res(response)

    @Utils.handle_exception(3, False)
    def leave_review(self, asset_id, cookie, review_message, user_agent, csrf_token, client):
        """
        Leave a review when bought
        """
        req_url = f"https://apis.roblox.com/asset-reviews-api/v1/assets/{asset_id}/comments"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
        req_json = {"text": review_message, "parentId": None}

        response = client.post(req_url, headers=req_headers, json=req_json, cookies=req_cookies)

        reviewed = response.status_code == 201

        return reviewed, response

