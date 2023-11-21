from Tool import Tool
import httpc
import concurrent.futures
from utils import Utils

class FriendRequestBot(Tool):
    def __init__(self, app):
        super().__init__("Friend Request Bot", "Send a lot of friend requests to a user", 5, app)

    @Tool.handle_exit
    def run(self):
        user_id = self.config["user_id"]
        cookies = self.get_cookies(self.config["max_generations"])

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_friend_request, user_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_sent, response_text = future.result()
                except Exception as e:
                    is_sent, response_text = False, str(e)

                if is_sent:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_sent, "New requests")

    @Utils.handle_exception(3)
    def send_friend_request(self, user_id, cookie):
        """
        Send a friend request to a user
        """
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = f"https://friends.roblox.com/v1/users/{user_id}/request-friendship"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)

            response = client.post(req_url, headers=req_headers, cookies=req_cookies)

        try:
            success = (response.status_code == 200 and response.json()["success"])
        except Exception:
            raise Exception("Failed to access success key. " + Utils.return_res(response))

        return success, Utils.return_res(response)
