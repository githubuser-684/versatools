import random
import string
import concurrent.futures
import requests
from Tool import Tool
from CaptchaSolver import CaptchaSolver

class CookieGenerator(Tool):
    def __init__(self, app):
        super().__init__("Cookie Generator", "Generates Roblox Cookies.", 2, app)
        
        self.max_generations = self.config["max_generations"]
        self.captcha_solver = self.config["captcha_solver"]
        self.use_proxy = self.config["use_proxy"]
        self.max_workers = self.config["max_workers"]

    def run(self):
        # open cookies.txt for writing in it
        f = open(self.cookies_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = 0

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                if (self.max_generations is None):
                    gen = 1000
                else:
                    gen = self.max_generations - worked_gen
                    if gen == 0:
                        break

                results = [executor.submit(self.generate_cookie, self.captcha_solver, self.use_proxy) for gen in range(gen)]

                for future in concurrent.futures.as_completed(results):
                    error, cookie = future.result()

                    if error == None:
                        worked_gen += 1
                        f.write(cookie+"\n")
                    else:
                        failed_gen += 1

                    total_gen += 1

                    print("\033[1A\033[K\033[1A\033[K\033[1;32mWorking: "+str(worked_gen)+"\033[0;0m | \033[1;31mFailed: "+str(failed_gen)+"\033[0;0m | \033[1;34mTotal: "+str(total_gen) + "\033[0;0m")
                    print("\033[1;31m" + str(error) + "\033[0;0m" if error != None else "\033[1;32mGenerated: " + cookie + "\033[0;0m")
        f.close()

    def get_csrf_token(self, proxies:dict = None) -> str:
        csrf_response = requests.post("https://auth.roblox.com/v2/login", proxies=proxies)
        csrf_token = csrf_response.headers.get("x-csrf-token")
        return csrf_token
    
    def generate_username(self):
        """
        Generates a random unique username
        """
        usernames = ['NebulaDreamer','ChromaStrike','LuminyLegend','CipherWhisper','ZenithEclipse','StelSerenade','PhantomNova','VanguardValor','RadiantRhythm','ElysianEnigma','LuminousLore','ArcaneAria','EtherealEssence','SeraphicShadow','RadiantSpecter','MysticWhisper','EmberSylph','AstralSymphony','ZephyrWanderer','EnigmaEcho','NexusVortex','ShadowSilhouette','AstralWhisper','LuminescentLuna','CipherSorcerer','RadiantReverie','EmberEthereal','SereneSpecter','ArcaneAurora','MysticMarauder','NebulaNight','Celestial','ChromaticChaos','ZenithZephyr','ElysianEnchant','LumiLabyrinth','PhantomPulse','VanVortex']
        
        generated_username = usernames[random.randint(0, len(usernames)-1)] + str(random.randint(0,9999))

        return generated_username
    
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
    
    def send_signup_request(self, user_agent:str, csrf_token:str, username:str, password:str, birthday:str, is_girl:bool, proxies:dict=None):
        req_url = "https://auth.roblox.com/v2/signup"
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}
        req_json={"birthday": birthday, "gender": 1 if is_girl else 2, "isTosAgreementBoxChecked": True, "password": password, "username": username}
        return requests.post(req_url, headers=req_headers, json=req_json, proxies=proxies)

    def generate_cookie(self, captcha_service:str, use_proxy:bool) -> tuple:
        """
        Generates a ROBLOSECURITY cookie
        Returns a tuple with the error and the cookie
        """
        try:
            captcha_solver = CaptchaSolver(captcha_service, self.captcha_tokens[captcha_service])
            user_agent = self.get_random_user_agent()
            proxies = self.get_random_proxies() if use_proxy else None
            csrf_token = self.get_csrf_token(proxies)

            username = self.generate_username()
            password = self.generate_password()
            birthday = self.generate_birthday()
            is_girl = random.choice([True, False])
            
            sign_up_req = self.send_signup_request(user_agent, csrf_token, username, password, birthday, is_girl, proxies)
            sign_up_res = captcha_solver.solve_captcha(sign_up_req, "ACTION_TYPE_WEB_SIGNUP", user_agent, csrf_token, proxies)
            
            cookie = sign_up_res.headers.get("Set-Cookie").split(".ROBLOSECURITY=")[1].split(";")[0]
        
        except Exception as e:
            return str(e), None
        
        return None, cookie