import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils
import random

class MessageBot(Tool):
    def __init__(self, app):
        super().__init__("Message Bot", "Spam someone with the same message or send messages to a large audience", 6, app)
        
        self.config["max_workers"]
        self.config["use_proxy"]

    def run(self):        
        print("Write the message you want to send.")
        subject = input("Subject: ")
        body = input("Body: ")

        print("1. Spam a specific user")
        print("2. Send to a large audience")
        
        askAgain = True
        while askAgain:
            choice = input("\033[0;0mEnter your choice: ")

            if (choice.isnumeric() and int(choice) > 0 and int(choice) < 3):
                choice = int(choice)
                askAgain = False

            if askAgain:
                print("\033[0;33mInvalid choice\033[0;0m")
        
        if (choice == 1):
            self.spam_specific_user(subject, body)
        
        if (choice == 2):
            print("Sorry, this feature is not available yet.")

    def spam_specific_user(self, subject, body):
        recipient_id = input("Recipient ID: ")

        cookies = self.get_cookies()

        msg_sent = 0
        msg_failed = 0
        total_cookies = len(cookies)

        print("Please wait... \n")

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

    @Utils.retry_on_exception()
    def allow_sending_msgs(self, cookie, proxies, user_agent, csrf_token):
        req_url = "https://apis.roblox.com/user-settings-api/v1/user-settings"
        req_cookies = {".ROBLOSECURITY": cookie, "RBXEventTrackerV2":f"browserid={random.randint(190000000,200000000)}"}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_json={"whoCanMessageMe": "All"}

        response = httpx.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)
    
        if (response.status_code != 200):
            raise Exception(response.text)

    @Utils.retry_on_exception()
    def send_message(self, subject, body, recipient_id, cookie)  -> (bool, str):
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        req_url = "https://privatemessages.roblox.com/v1/messages/send"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_json={"body": body, "recipientid": recipient_id, "subject": subject}

        response = httpx.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)

        if (not response.json()["success"] and response.json()["shortMessage"] == "SenderPrivacySettingsTooHigh"):
            self.allow_sending_msgs(cookie, proxies, user_agent, csrf_token)
            # try again
            response = httpx.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)

        return (response.status_code == 200 and response.json()["success"]), response.text