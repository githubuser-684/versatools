import random
import string
import concurrent.futures
import httpx
from Tool import Tool
from CaptchaSolver import CaptchaSolver
from utils import Utils
from data.adjectives import adjectives
from data.nouns import nouns

class CookieGenerator(Tool):
    def __init__(self, app):
        super().__init__("Cookie Generator", "Generates Roblox Cookies.", 2, app)

        self.config["max_generations"]
        self.config["captcha_solver"]
        self.config["use_proxy"]
        self.config["max_workers"]

    def run(self):
        # open cookies.txt for writing in it
        f = open(self.cookies_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = self.config["max_generations"]

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            results = [executor.submit(self.generate_cookie, self.config["captcha_solver"], self.config["use_proxy"]) for gen in range(self.config["max_generations"])]

            for future in concurrent.futures.as_completed(results):
                try:
                    cookie = future.result()
                    worked_gen += 1
                    f.write(cookie+"\n")
                    response_text = cookie
                    has_worked = True
                except Exception as e:
                    has_worked = False
                    failed_gen += 1
                    response_text = str(e)

                self.print_status(worked_gen, failed_gen, total_gen, response_text, has_worked, "Generated")
        f.close()

    @Utils.retry_on_exception()
    def get_csrf_token(self, proxies:dict = None) -> str:
        csrf_response = httpx.post("https://auth.roblox.com/v2/login", proxies=proxies)
        csrf_token = csrf_response.headers.get("x-csrf-token")
        return csrf_token
    
    def generate_username(self):
        word1 = random.choice(adjectives)
        word2 = random.choice(nouns)
        word1 = word1.title()
        word2 = word2.title()
        generated_username = '{}{}{}'.format(word1, word2, random.randint(1, 99))

        return generated_username
    
    def verify_username(self, user_agent:str, csrf_token:str, username:str, birthday: str, proxies:dict=None):
        req_url = "https://auth.roblox.com/v1/usernames/validate"
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        req_json={"birthday": birthday, "context": "Signup", "username": username}

        response = httpx.post(req_url, headers=req_headers, json=req_json, proxies=proxies)

        return response.json()["message"] == "Username is valid", response.json()["message"]

    def generate_password(self):
        """
        Generates a random and complex password
        """
        length = 10
        return ''.join(random.choices(string.ascii_uppercase + string.digits + string.punctuation, k=length))
    
    def generate_birthday(self):
        """
        Generates a random birthday
        """
        return str(random.randint(2006, 2010)).zfill(2) + "-" + str(random.randint(1, 12)).zfill(2) + "-" + str(random.randint(1, 27)).zfill(2) + "T05:00:00.000Z"
    
    @Utils.retry_on_exception()
    def send_signup_request(self, user_agent:str, csrf_token:str, username:str, password:str, birthday:str, is_girl:bool, proxies:dict=None):
        req_url = "https://auth.roblox.com/v2/signup"
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        req_json={"birthday": birthday, "gender": 1 if is_girl else 2, "isTosAgreementBoxChecked": True, "password": password, "username": username}
        return httpx.post(req_url, headers=req_headers, json=req_json, proxies=proxies)

    def generate_cookie(self, captcha_service:str, use_proxy:bool) -> tuple:
        """
        Generates a ROBLOSECURITY cookie
        Returns a tuple with the error and the cookie
        """
        captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
        user_agent = self.get_random_user_agent()
        proxies = self.get_random_proxies() if use_proxy else None
        csrf_token = self.get_csrf_token(proxies)

        birthday = self.generate_birthday()

        retry_count = 0
        while retry_count < 3:
            username = self.generate_username()
            is_username_valid, response_text = self.verify_username(user_agent, csrf_token, username, birthday, proxies)

            if is_username_valid:
                break
            
            retry_count += 1

        if not is_username_valid:
            raise Exception(f"Failed to generate a valid username after 3 retries. ({response_text})")

        password = self.generate_password()
        is_girl = random.choice([True, False])

        sign_up_req = self.send_signup_request(user_agent, csrf_token, username, password, birthday, is_girl, proxies)
        sign_up_res = captcha_solver.solve_captcha(sign_up_req, "ACTION_TYPE_WEB_SIGNUP", user_agent, proxies)

        cookie = sign_up_res.headers.get("Set-Cookie").split(".ROBLOSECURITY=")[1].split(";")[0]
        
        return cookie