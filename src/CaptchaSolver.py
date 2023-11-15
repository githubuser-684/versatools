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

class CaptchaSolver(Proxy):
    def __init__(self, captcha_service:str, api_key:str):
        super().__init__()

        self.captcha_service = captcha_service.lower()
        self.api_key = api_key

    def get_rblx_public_key(self, action_type):
        """
        Gets the public key for the specified action type
        """
        return public_keys[action_type]

    def solve_captcha(self, response:httpx.Response, action_type:str, user_agent:str, client) -> httpx.Response:
        """
        Resolves a Roblox "Challenge is required..." request using the specified captcha service.
        Returns the captcha bypassed response from the request.
        """
        status_code = response.status_code
        response_headers = response.headers

        if status_code == 423: # rate limited
            raise Exception(Utils.return_res(response))
        elif status_code != 403: # no captcha
            return response

        # get captcha data
        rblx_challenge_id = response_headers["Rblx-Challenge-Id"]
        rblx_metadata = json.loads(base64.b64decode(response_headers["Rblx-Challenge-Metadata"]))
        blob = rblx_metadata["dataExchangeBlob"]
        unified_captcha_id = rblx_metadata["unifiedCaptchaId"]
        public_key = self.get_rblx_public_key(action_type)
        website_url = "https://www.roblox.com"
        website_subdomain = "roblox-api.arkoselabs.com"

        # solve captcha using specified service
        if self.captcha_service == "anti-captcha":
            solver = funcaptchaProxyless() # funcaptchaProxyon()
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
            captcha_response = httpx.post('https://capbypass.com/api/createTask', json={
                "clientKey": self.api_key,
                "task": {
                    "type":"FunCaptchaTask",
                    "websiteURL": website_url,
                    "websitePublicKey": public_key,
                    "websiteSubdomain": website_subdomain,
                    "data[blob]": blob,
                    "proxy": ""
                }
            }, timeout=120)

            try:
                result = captcha_response.json()
                token = result["solution"]["token"]
            except json.JSONDecodeError:
                raise Exception(Utils.return_res(captcha_response))
            except Exception:
                if captcha_response.json().get("error") == "Key doesn't exist.":
                    raise Exception("Valid capbypass API key is required.")

                raise Exception(Utils.return_res(captcha_response))
        else:
            raise Exception("Captcha service not supported yet. Supported: anti-captcha, 2captcha, capsolver, capbypass")

        # build metadata containing token for login request
        metadata = f"{{\"unifiedCaptchaId\":\"{unified_captcha_id}\",\"captchaToken\":\"{token}\",\"actionType\":\"{rblx_metadata['actionType']}\"}}"
        metadata_base64 = base64.b64encode(metadata.encode()).decode()

        # get headers from response
        req_headers = json.loads((str(response.request.headers).replace("Headers(", "")[:-1]).replace("'", '"'))
        del req_headers["content-length"]

        # challenge_continue
        req_url = "https://apis.roblox.com/challenge/v1/continue"
        ua = req_headers["user-agent"]
        csrf_token = req_headers["x-csrf-token"]
        continue_headers = self.get_roblox_headers(ua, csrf_token)
        req_json={"challengeId": rblx_challenge_id, "challengeMetadata": metadata, "challengeType": "captcha"}

        client.post(req_url, headers=continue_headers, json=req_json)

        # send request again but with captcha token
        req_url = str(response.request.url)

        req_headers['Rblx-Challenge-Id'] = rblx_challenge_id
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
        req_json["captchaId"] = unified_captcha_id
        req_json["captchaProvider"] = "PROVIDER_ARKOSE_LABS"

        final_response = client.post(req_url, headers=req_headers, json=req_json, data=req_data)

        return final_response

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
            req_url = 'https://capbypass.com/api/getBalance'
            req_data = {
                'clientKey': self.api_key,
            }

            response = httpx.post(req_url, json=req_data)
            balance = response.json()["balance"]
            return balance
        else:
            raise Exception("Captcha service not found")

        return balance

    def __str__(self):
        return "A funcaptcha Solver using " + self.captcha_service + " as the captcha service."
