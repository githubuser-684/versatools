import random
import string
import concurrent.futures
import httpc
import eel
from Tool import Tool
from CaptchaSolver import CaptchaSolver
from utils import Utils
from data.adjectives import adjectives
from data.nouns import nouns

class CookieGenerator(Tool):
    def __init__(self, app):
        super().__init__("Cookie Generator", "Generates Roblox Cookies.", 2, app)

    def run(self):
        eel.write_terminal("\x1B[1;33mWarning: Cookies generated using our tool are flagged and region locked.\x1B[0;0m")

        # open cookies.txt for writing in it
        f = open(self.cookies_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = self.config["max_generations"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            self.results = [executor.submit(self.generate_cookie, self.config["captcha_solver"], self.config["use_proxy"]) for gen in range(self.config["max_generations"])]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue

                try:
                    has_generated, response_text = future.result()
                except Exception as e:
                    has_generated, response_text = False, str(e)

                if has_generated:
                    worked_gen += 1
                    f.write(response_text+"\n")
                    f.flush()
                else:
                    failed_gen += 1

                self.print_status(worked_gen, failed_gen, total_gen, response_text, has_generated, "Generated")
        f.close()

    @Utils.handle_exception(2, False)
    def verify_username(self, user_agent:str, csrf_token:str, username:str, birthday: str, client):
        """
        Verifies if a username is valid
        """
        req_url = "https://auth.roblox.com/v1/usernames/validate"
        req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
        req_json={"birthday": birthday, "context": "Signup", "username": username}

        response = client.post(req_url, headers=req_headers, json=req_json)

        if response.status_code != 200:
            raise Exception(Utils.return_res(response))

        try:
            message = response.json()["message"]
        except KeyError:
            raise Exception("Unable to access message key " + Utils.return_res(response))

        return message == "Username is valid", message

    def generate_username(self):
        """
        Generates a random username
        """
        word1 = random.choice(adjectives)
        word2 = random.choice(nouns)
        word1 = word1.title()
        word2 = word2.title()
        generated_username = f"{word1}{word2}{random.randint(1, 9999)}"

        return generated_username

    def generate_password(self):
        """
        Generates a random and complex password
        """
        length = 10
        password = ''.join(random.choices(string.ascii_uppercase + string.digits + string.punctuation, k=length))
        password.replace(":", "v")

        return password

    def generate_birthday(self):
        """
        Generates a random birthday
        """
        return str(random.randint(2006, 2010)).zfill(2) + "-" + str(random.randint(1, 12)).zfill(2) + "-" + str(random.randint(1, 27)).zfill(2) + "T05:00:00.000Z"

    @Utils.handle_exception(3, False)
    def send_signup_request(self, user_agent:str, csrf_token:str, username:str, password:str, birthday:str, is_girl:bool, client):
        """
        Sends a signup request to the auth.roblox.com endpoint
        """
        req_url = "https://auth.roblox.com/v2/signup"
        req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
        req_json={"birthday": birthday, "gender": 1 if is_girl else 2, "isTosAgreementBoxChecked": True, "password": password, "username": username}
        result = client.post(req_url, headers=req_headers, json=req_json)

        return result

    @Utils.handle_exception()
    def generate_cookie(self, captcha_service:str, use_proxy:bool) -> tuple:
        """
        Generates a ROBLOSECURITY cookie
        Returns a tuple with the error and the cookie
        """
        proxies = self.get_random_proxy() if use_proxy else None

        with httpc.Session(proxies=proxies, spoof_tls=True) as client:
            captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(None, client)

            birthday = self.generate_birthday()

            retry_count = 0
            while retry_count < 5:
                username = self.generate_username()
                is_username_valid, response_text = self.verify_username(user_agent, csrf_token, username, birthday, client)

                if is_username_valid:
                    break

                retry_count += 1

            if not is_username_valid:
                raise Exception(f"Failed to generate a valid username after {retry_count} tries. ({response_text})")

            password = self.generate_password()
            is_girl = random.choice([True, False])

            sign_up_req = self.send_signup_request(user_agent, csrf_token, username, password, birthday, is_girl, client)
            sign_up_res = captcha_solver.solve_captcha(sign_up_req, "ACTION_TYPE_WEB_SIGNUP", client)

        try:
            cookie = httpc.extract_cookie(sign_up_res, ".ROBLOSECURITY")
        except Exception:
            raise Exception(Utils.return_res(sign_up_res))

        return True, f"{username}:{password}:{cookie}"
