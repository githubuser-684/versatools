import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils
import random
import string
import time
import mailparser
from urllib.parse import unquote

class CookieVerifier(Tool):
    def __init__(self, app):
        super().__init__("Cookie Verifier", "Verify your cookies!", 4, app)

    def run(self):
        cookies = self.get_cookies()

        req_worked = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.verify_cookie, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_verified, response_text = future.result()
                except Exception as e:
                    is_verified, response_text = False, str(e)

                if is_verified:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, is_verified, "Verified")

    @Utils.retry_on_exception()
    def is_verified(self, cookie, user_agent, proxies):
        """
        Checks if a cookie is verified
        """
        req_url = "https://accountsettings.roblox.com/v1/email"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent)

        response = httpx.get(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)

        return response.json()["verified"]

    @Utils.retry_on_exception()
    def create_address(self, proxies):
        """
        Creates a random email address
        """
        # get domain
        req_url = "https://api.mail.tm/domains"
        response = httpx.get(req_url, proxies=proxies)

        if response.status_code != 200:
            raise Exception(f"Failed to get domain {response.text} Code: {response.status_code}")

        domain = response.json()["hydra:member"][0]["domain"]

        # create email address
        address = ( ''.join(random.choice(string.ascii_lowercase) for i in range(10)) ) + "@" + domain
        req_url = "https://api.mail.tm/accounts"
        req_json = {"address": address, "password": "versatools"}
        response = httpx.post(req_url, json=req_json, proxies=proxies)

        if response.status_code != 201:
            raise Exception(f"Failed to create email {response.text} Code: {response.status_code}")

        address = response.json()["address"]

        # get auth token
        req_url = "https://api.mail.tm/token"
        req_json = {"address": address, "password": "versatools"}
        response = httpx.post(req_url, json=req_json, proxies=proxies)
        token = response.json()["token"]

        if response.status_code != 200:
            raise Exception(f"Failed to get token {response.text} Code: {response.status_code}")

        return address, token

    @Utils.retry_on_exception()
    def set_roblox_email(self, cookie, user_agent, proxies, csrf_token, email_addr):
        """
        Sets the roblox email address
        """
        req_url = "https://accountsettings.roblox.com/v1/email"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_json={"emailAddress": email_addr}

        response = httpx.post(req_url, headers=req_headers, cookies=req_cookies, json=req_json, proxies=proxies)

        return response.status_code == 200, response.text

    @Utils.retry_on_exception(10)
    def get_email_id(self, token, proxies):
        """
        Gets the id of the latest email
        """
        time.sleep(1.5)
        req_url = "https://api.mail.tm/messages"
        req_params = {"page": 1}
        req_headers = {"Authorization": f"Bearer {token}"}
        response = httpx.get(req_url, params=req_params, headers=req_headers, proxies=proxies)

        if response.status_code != 200:
            raise Exception(f"Failed to get email id {response.text}")

        mails = response.json()["hydra:member"]

        if len(mails) == 0:
            raise Exception("No mails found")

        return mails[0]["id"]

    @Utils.retry_on_exception()
    def get_email(self, token, mail_id, proxies):
        """
        Gets the email
        """
        req_url = f"https://api.mail.tm/sources/{mail_id}"
        req_headers = {"Authorization": f"Bearer {token}"}
        response = httpx.get(req_url, headers=req_headers, proxies=proxies)

        if response.status_code != 200:
            raise Exception(f"Failed to get email {response.text}")

        data = response.json()["data"]
        mail = mailparser.parse_from_string(data)

        return mail

    @Utils.retry_on_exception()
    def click_verif_link(self, mail, cookie, user_agent, csrf_token, proxies):
        """
        Simulates clicking on the verification link
        """
        ticket = unquote(mail.body.split("?ticket=")[1].split('"')[0])

        req_url = "https://accountinformation.roblox.com/v1/email/verify"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = self.get_roblox_headers(user_agent, csrf_token)
        req_json = {"ticket": ticket}
        response = httpx.post(req_url, json=req_json, headers=req_headers, cookies=req_cookies, proxies=proxies)

        if response.status_code != 200:
            raise Exception(f"Failed to click verification link {response.text}")

    @Utils.retry_on_exception()
    def verify_cookie(self, cookie:str):
        """
        Verifies a cookie
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        # make sure email is not already verified
        is_verified = self.is_verified(cookie, user_agent, proxies)
        if is_verified:
            return True, "Email is already verified"

        address, token = self.create_address(proxies)

        # set roblox email
        is_valid, response_text = self.set_roblox_email(cookie, user_agent, proxies, csrf_token, address)
        if not is_valid:
            return False, response_text

        # get roblox email
        mail_id = self.get_email_id(token, proxies)
        mail = self.get_email(token, mail_id, proxies)
        # click on verification link
        self.click_verif_link(mail, cookie, user_agent, csrf_token, proxies)

        return True, "The email address has been verified."
