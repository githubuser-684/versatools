import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils

class ModelVote(Tool):
    def __init__(self, app):
        super().__init__("Model Vote", "Increase Like/Dislike count of a model", 1, app)

    def run(self):
        model_id = self.config["model_id"]
        vote = not self.config["dislike"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_model_vote, model_id, vote, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "New votes")

    @Utils.retry_on_exception()
    def send_model_vote(self, model_id, vote, cookie):
        """
        Send a vote to a model
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        req_url = f"https://www.roblox.com/voting/vote?assetId={model_id}&vote={'true' if vote else 'false'}"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)

        response = httpx.post(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)

        return (response.status_code == 200 and response.json()["Success"]), Utils.return_res(response)