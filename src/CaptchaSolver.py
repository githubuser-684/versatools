import base64
from anticaptchaofficial.funcaptchaproxyless import *
from anticaptchaofficial.funcaptchaproxyon import *
from twocaptcha import TwoCaptcha
import capsolver
from utils import Suppressor, Utils
import httpx
from urllib.parse import unquote
from Proxy import Proxy
from data.public_keys import public_keys
import random

class CaptchaSolver(Proxy):
    def __init__(self, captcha_service:str, api_key:str):
        super().__init__()

        self.captcha_service = captcha_service.lower()
        self.api_key = api_key

    def solve_captcha(self, response:httpx.Response, action_type:str, user_agent:str, client) -> httpx.Response:
        """
        Resolves a Roblox "Challenge is required..." request using the specified captcha service.
        Returns the captcha bypassed response from the request.
        """
        if response.status_code == 423: # rate limited
            raise Exception(Utils.return_res(response))
        elif response.status_code != 403: # no captcha
            return response

        metadata = response.headers["Rblx-Challenge-Metadata"]
        blob, captcha_id, meta_action_type = self.get_captcha_data(metadata)

        public_key = public_keys[action_type]
        website_url = "https://www.roblox.com"
        website_subdomain = "roblox-api.arkoselabs.com"

        # solve captcha using specified service
        token = self.send_to_solver(website_url, website_subdomain, public_key, blob, user_agent)

        metadata, metadata_base64 = self.build_metadata(captcha_id, token, meta_action_type)

        # get headers from response
        req_headers = json.loads((str(response.request.headers).replace("Headers(", "")[:-1]).replace("'", '"'))
        del req_headers["content-length"]

        # challenge_continue
        self.challenge_continue(req_headers, captcha_id, metadata, client)

        # send request again but with captcha token
        req_url, req_headers, req_json, req_data = self.build_captcha_res(response, req_headers, captcha_id, metadata_base64, token)

        final_response = client.post(req_url, headers=req_headers, json=req_json, data=req_data)

        return final_response

    def get_captcha_data(self, metadata_base64):
        metadata = json.loads(base64.b64decode(metadata_base64))
        blob = metadata["dataExchangeBlob"]
        unified_captcha_id = metadata["unifiedCaptchaId"]
        action_type = metadata["actionType"]

        return blob, unified_captcha_id, action_type

    def send_to_solver(self, website_url, website_subdomain, public_key, blob, user_agent):
        if self.captcha_service == "anti-captcha":
            solver = funcaptchaProxyless()
            solver.set_verbose(0)
            solver.set_key(self.api_key)
            solver.set_website_url(website_url)
            solver.set_website_key(public_key)
            solver.set_data_blob('{"blob":"' + blob + '"}')
            solver.set_soft_id(0)

            token = solver.solve_and_return_solution()

            if token == 0:
                raise Exception("task finished with error " + solver.error_code)
        elif self.captcha_service == "2captcha":
            solver = TwoCaptcha(self.api_key)

            result = solver.funcaptcha(
                sitekey=public_key,
                url=website_url,
                userAgent=user_agent,
                **{"data[blob]": blob}
            )

            token = result["code"]
        elif self.captcha_service == "capsolver":
            capsolver.api_key = self.api_key
            with Suppressor():
                solution = capsolver.solve({
                    "type": "FunCaptchaTaskProxyLess",
                    "websitePublicKey": public_key,
                    "websiteURL": website_url,
                    "data": f"{{\"blob\":\"{blob}\"}}"
                })

            token = solution["token"]
        elif self.captcha_service == "capbypass":
            captcha_response = httpx.post('https://api.capbypass.com/createTask', json={
                "clientKey": self.api_key,
                "task": {
                    "type":"FunCaptchaTaskProxyLess",
                    "websiteURL": website_url,
                    "websitePublicKey": public_key,
                    "funcaptchaApiJSSubdomain": "https://"+website_subdomain,
                    "data": "{\"blob\": \""+blob+"\"}"
                }
            })

            result = captcha_response.json()

            try:
                taskId = result["taskId"]
                taskStatus = result["status"]
            except Exception:
                if result.get("errorDescription") == "Invalid Key":
                    raise Exception("Invalid Capbypass API key")

                raise Exception(Utils.return_res(captcha_response))

            # polling
            # wait for captcha to be solved
            tries = 20
            while taskStatus in ["idle", "processing"] and tries > 0:
                captcha_response = httpx.post('https://api.capbypass.com/getTaskResult', json={
                    "clientKey": self.api_key,
                    "taskId": taskId
                })

                result = captcha_response.json()
                try:
                    taskStatus = result["status"]
                except Exception:
                    raise Exception(Utils.return_res(captcha_response))

                tries -= 1
                time.sleep(1)

            if taskStatus in ["idle", "processing"]:
                raise Exception("Captcha timed out")

            try:
                token = result["solution"]
            except Exception:
                raise Exception(Utils.return_res(captcha_response))
        else:
            raise Exception("Captcha service not supported yet. Supported: anti-captcha, 2captcha, capsolver, capbypass")

        return token

    def build_metadata(self, unified_captcha_id, token, action_type):
        metadata = f"{{\"unifiedCaptchaId\":\"{unified_captcha_id}\",\"captchaToken\":\"{token}\",\"actionType\":\"{action_type}\"}}"
        metadata_base64 = base64.b64encode(metadata.encode()).decode()

        return metadata, metadata_base64

    def challenge_continue(self, req_headers, captcha_id, metadata, client):
        req_url = "https://apis.roblox.com/challenge/v1/continue"

        ua = req_headers["user-agent"]
        csrf_token = req_headers["x-csrf-token"]
        cookie = req_headers["cookie"]
        continue_headers = self.get_roblox_headers(ua, csrf_token)
        continue_headers["Cookie"] = cookie

        req_json={"challengeId": captcha_id, "challengeMetadata": metadata, "challengeType": "captcha"}

        result = client.post(req_url, headers=continue_headers, json=req_json)

        if result.status_code != 200:
            raise Exception(Utils.return_res(result))

    def build_captcha_res(self, response, req_headers, captcha_id, metadata_base64, token):
        req_url = str(response.request.url)

        req_headers['Rblx-Challenge-Id'] = captcha_id
        req_headers["Rblx-Challenge-Type"] = "captcha"
        req_headers["Rblx-Challenge-Metadata"] = metadata_base64

        # error bytes to json
        req_json = {}
        req_data = {}

        req_content = bytes.decode(response.request._content)

        if response.request.headers["content-type"] == "application/x-www-form-urlencoded":
            pairs = req_content.split('&')
            for pair in pairs:
                key, value = pair.split('=')
                req_data[key] = unquote(value).replace('+', ' ')
        else:
            req_json = json.loads(req_content) if req_content != "" else {}

        req_json["captchaToken"] = token
        req_json["captchaId"] = captcha_id
        req_json["captchaProvider"] = "PROVIDER_ARKOSE_LABS"

        return req_url, req_headers, req_json, req_data

    def get_balance(self):
        """
        Gets the balance of the captcha service
        """
        if self.captcha_service == "anti-captcha":
            solver = funcaptchaProxyless() # or any other class
            solver.set_verbose(0)
            solver.set_key(self.api_key)
            balance = solver.get_balance()
        elif self.captcha_service == "2captcha":
            solver = TwoCaptcha(self.api_key)
            balance = solver.balance()
        elif self.captcha_service == "capsolver":
            capsolver.api_key = self.api_key

            with Suppressor():
                balance = capsolver.balance()["balance"]
        elif self.captcha_service == "capbypass":
            req_url = 'https://api.capbypass.com/getBalance'
            req_data = {
                'clientKey': self.api_key,
            }

            response = httpx.post(req_url, json=req_data)
            try:
                balance = response.json()["balance"]
            except Exception:
                raise Exception(Utils.return_res(response))
            return balance
        else:
            raise Exception("Captcha service not found")

        return balance

    def __str__(self):
        return "A funcaptcha Solver using " + self.captcha_service + " as the captcha service."
