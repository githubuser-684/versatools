import httpc
from Tool import Tool
import concurrent.futures
from CaptchaSolver import CaptchaSolver
from utils import Utils

class GroupAllyBot(Tool):
    def __init__(self, app):
        super().__init__("Group Ally Bot", "Mass send ally requests to groups", 6, app)

    @Tool.handle_exit
    def run(self):
        cookie = self.config["cookie"]
        start_group_id = self.config["start_group_id"]
        your_group_id = self.config["your_group_id"]
        max_generations = self.config["max_generations"]

        req_worked = 0
        req_failed = 0
        total_req = max_generations

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_ally_request, your_group_id, cookie, i+int(start_group_id)) for i in range(max_generations)]

            for future in concurrent.futures.as_completed(results):
                try:
                    has_req, response_text = future.result()
                except Exception as e:
                    has_req, response_text =  False, str(e)

                if has_req:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, has_req, "Ally Requested")

    @Utils.handle_exception()
    def send_ally_request(self, your_group_id, cookie, group_id_to_ally):
        """
        Send a ally request to a group
        """

        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = f"https://groups.roblox.com/v1/groups/{your_group_id}/relationships/allies/{group_id_to_ally}"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)

            response = client.post(req_url, headers=req_headers, cookies=req_cookies)

        return (response.status_code == 200), Utils.return_res(response)
