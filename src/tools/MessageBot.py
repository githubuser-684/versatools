import httpc
from Tool import Tool
import concurrent.futures
from utils import Utils
import random

class MessageBot(Tool):
    def __init__(self, app):
        super().__init__("Message Bot", "Spam someone with the same message", 6, app)

    @Tool.handle_exit
    def run(self):
        subject = self.config["subject"]
        body = self.config["body"]

        self.spam_specific_user(subject, body)

    def spam_specific_user(self, subject, body):
        """
        Spam a specific user with the same message
        """
        recipient_id = self.config["recipient_id"]
        cookies = self.get_cookies(self.config["max_generations"])

        msg_sent = 0
        msg_failed = 0
        total_cookies = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_message, subject, body, recipient_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_sent, response_text = future.result()
                except Exception as e:
                    is_sent, response_text = False, str(e)

                if is_sent:
                    msg_sent += 1
                else:
                    msg_failed += 1

                self.print_status(msg_sent, msg_failed, total_cookies, response_text, is_sent, "Messages sent")

    @Utils.handle_exception(3, False)
    def allow_sending_msgs(self, cookie, client, user_agent, csrf_token):
        """
        Allow sending messages to anyone
        """
        req_url = "https://apis.roblox.com/user-settings-api/v1/user-settings"
        req_cookies = {".ROBLOSECURITY": cookie, "RBXEventTrackerV2":f"browserid={random.randint(190000000,200000000)}"}
        req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
        req_json={"whoCanMessageMe": "All"}

        response = client.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json)

        if response.status_code != 200:
            raise Exception(Utils.return_res(response))

    @Utils.handle_exception(3)
    def send_message(self, subject, body, recipient_id, cookie)  -> (bool, str):
        """
        Send a message to a user
        """
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)

            req_url = "https://privatemessages.roblox.com/v1/messages/send"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
            req_json={"body": body, "recipientid": recipient_id, "subject": subject}

            response = client.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json)

            if (not response.json()["success"] and response.json()["shortMessage"] == "SenderPrivacySettingsTooHigh"):
                self.allow_sending_msgs(cookie, client, user_agent, csrf_token)
                # try again
                response = client.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json)

        try:
            success = response.status_code == 200 and response.json()["success"]
        except Exception:
            raise Exception("Failed to access success key" + Utils.return_res(response))

        return success, Utils.return_res(response)
