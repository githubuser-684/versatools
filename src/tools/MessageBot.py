import time
import requests
from Tool import Tool
import concurrent.futures

class MessageBot(Tool):
    def __init__(self, app):
        super().__init__("Message Bot", "Spam someone with the same message or send messages to a large audience", 6, app)
        
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

        self.cookies_file_path = self.app.cookies_file_path

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

        f = open(self.cookies_file_path, 'r+')
        cookies = f.read().splitlines()
        f.close()

        msg_sent = 0
        msg_failed = 0
        total_cookies = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.send_message, subject, body, recipient_id, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                is_sent, response_text = future.result()

                if is_sent:
                    msg_sent += 1
                else:
                    msg_failed += 1

                print("\033[1A\033[K\033[1A\033[K\033[1;32mSent: "+str(msg_sent)+"\033[0;0m | \033[1;31mFailed: "+str(msg_failed)+"\033[0;0m | \033[1;34mTotal: "+str(total_cookies) + "\033[0;0m")
                print("\033[1;32mWorked: " + response_text + "\033[0;0m" if is_sent else "\033[1;31mFailed: " + response_text + "\033[0;0m")          

    
    def send_message(self, subject, body, recipient_id, cookie)  -> (bool, str):
        err = None
        for _ in range(3):
            try:
                proxies = self.get_random_proxies() if self.use_proxy else None
                user_agent = self.get_random_user_agent()
                csrf_token = self.get_csrf_token(proxies, cookie)

                req_url = "https://privatemessages.roblox.com:443/v1/messages/send"
                req_cookies = {".ROBLOSECURITY": cookie}
                req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
                req_json={"body": body, "recipientid": recipient_id, "subject": subject}

                response = requests.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)
                break
            except Exception as e:
                err = str(e)
                time.sleep(2)
        else:
            return False, err
    
        return (response.status_code == 200 and response.json()["success"]), response.text