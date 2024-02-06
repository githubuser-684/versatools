import base64
import json
import time
from utils import Utils
import httpc
from Proxy import Proxy
from data.public_keys import public_keys

class CaptchaSolver(Proxy):
    def __init__(self, captcha_service:str, api_key:str):
        super().__init__()

        self.captcha_service = captcha_service.lower()
        self.api_key = api_key

    def solve_captcha(self, response, action_type:str, proxy_line:str, client):
        """
        Resolves a Roblox "Challenge is required..." request using the specified captcha service.
        Returns the captcha bypassed response from the request.
        """
        if response.status_code == 423: # rate limited
            raise Exception(Utils.return_res(response))
        elif response.status_code != 403: # no captcha
            return response

        try:
            metadata = response.headers["Rblx-Challenge-Metadata"]
            blob, captcha_id, meta_action_type = self.get_captcha_data(metadata)
        except KeyError:
            raise Exception(f"No metadata found. {Utils.return_res(response)}")

        public_key = public_keys[action_type]
        website_url = "https://www.roblox.com"
        website_subdomain = "roblox-api.arkoselabs.com"

        # solve captcha using specified service
        token = self.send_to_solver(website_url, website_subdomain, public_key, blob, proxy_line)

        metadata, metadata_base64 = self.build_metadata(captcha_id, token, meta_action_type)

        # challenge_continue
        self.challenge_continue(response.request, captcha_id, metadata, client)

        # send request again but with captcha token
        req_url, req_headers, req_json, req_data = self.build_captcha_res(response.request, captcha_id, metadata_base64, meta_action_type)

        final_response = client.post(req_url, headers=req_headers, json=req_json, data=req_data)

        return final_response

    def get_captcha_data(self, metadata_base64):
        metadata = json.loads(base64.b64decode(metadata_base64))
        blob = metadata["dataExchangeBlob"]
        unified_captcha_id = metadata["unifiedCaptchaId"]
        action_type = metadata["actionType"]

        return blob, unified_captcha_id, action_type

    def solve_capbypass(self, website_url, public_key, website_subdomain, blob, proxy):
        captcha_response = httpc.post('https://capbypass.com/api/createTask', json={
            "clientKey": self.api_key,
            "task": {
                "type": "FunCaptchaTaskProxyLess",
                "websiteURL": website_url,
                "websitePublicKey": public_key,
                "funcaptchaApiJSSubdomain": "https://"+website_subdomain,
                "data": "{\"blob\": \""+blob+"\"}",
                "proxy": proxy
            }
        })

        try:
            result = captcha_response.json()

            taskId = result["taskId"]
            errorId = result["errorId"]
        except Exception:
            raise Exception("create task error. " + Utils.return_res(captcha_response))

        if errorId != 0:
            raise Exception(Utils.return_res(captcha_response))

        # polling
        # wait for captcha to be solved
        tries = 50
        solution = None

        while not solution and tries > 0:
            captcha_response = httpc.post('https://capbypass.com/api/getTaskResult', json={
                "clientKey": self.api_key,
                "taskId": taskId
            })

            try:
                result = captcha_response.json()

                solution = result.get("solution")
                errorId = result["errorId"]
            except KeyError:
                raise Exception("get task error. " + Utils.return_res(captcha_response))

            if errorId != 0:
                raise Exception(Utils.return_res(captcha_response))

            tries -= 1
            time.sleep(1)

        return solution

    def send_to_solver(self, website_url, website_subdomain, public_key, blob, proxy_line):
        if self.captcha_service == "capbypass":
            token = self.solve_capbypass(website_url, public_key, website_subdomain, blob, proxy_line)
        else:
            raise Exception('Only "Capbypass" solver is working. Other services are not supported.')

        return token

    def build_metadata(self, unified_captcha_id, token, action_type):
        metadata = f"{{\"unifiedCaptchaId\":\"{unified_captcha_id}\",\"captchaToken\":\"{token}\",\"actionType\":\"{action_type}\"}}"
        metadata_base64 = base64.b64encode(metadata.encode()).decode()

        return metadata, metadata_base64

    def challenge_continue(self, init_req, captcha_id, metadata, client):
        req_url = "https://apis.roblox.com/challenge/v1/continue"

        user_agent = init_req["headers"]["User-Agent"]
        csrf_token = init_req["headers"]["X-Csrf-Token"]
        continue_headers = httpc.get_roblox_headers(user_agent, csrf_token)

        cookies = init_req.get("cookies")

        req_json={"challengeId": captcha_id, "challengeMetadata": metadata, "challengeType": "captcha"}

        result = client.post(req_url, headers=continue_headers, json=req_json, cookies=cookies)

        if result.status_code != 200:
            raise Exception(Utils.return_res(result))

    def build_captcha_res(self, init_req, captcha_id, metadata_base64, meta_action_type):
        req_url = init_req["url"]
        req_headers = init_req["headers"]

        req_headers['rblx-challenge-id'] = captcha_id
        req_headers["rblx-challenge-type"] = "captcha"
        req_headers["rblx-challenge-metadata"] = metadata_base64

        req_json = init_req.get("json")
        req_data = init_req.get("data")

        return req_url, req_headers, req_json, req_data

    def get_balance(self):
        """
        Gets the balance of the captcha service
        """
        if self.captcha_service == "capbypass":
            req_url = 'https://capbypass.com/api/getBalance'
            req_data = {
                'clientKey': self.api_key,
            }

            response = httpc.post(req_url, json=req_data)
            try:
                balance = response.json()["credits"]
            except KeyError:
                raise Exception(Utils.return_res(response))
        else:
            raise Exception("Captcha service not found. Only Capbypass is supported. Other services don't work.")

        return balance

    def __str__(self):
        return "A funcaptcha Solver using " + self.captcha_service + " as the captcha service."