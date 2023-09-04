import requests
from Tool import Tool
import concurrent.futures
from utils import Utils

class GameVote(Tool):
    def __init__(self, app):
        super().__init__("Game Vote", "Increase Like/Dislike count of a game", 1, app)

        self.max_generations = self.config["max_generations"]
        self.max_workers = self.config["max_workers"]
        self.use_proxy = self.config["use_proxy"]

        self.cookies_file_path = self.app.cookies_file_path

    def run(self):
        game_id = input("Game ID to like/dislike: ")

        print("1. Like")
        print("2. Dislike")
        
        ask_again = True
        while ask_again:
            choice = input("\033[0;0mEnter your choice: ")

            if (choice.isnumeric() and int(choice) > 0 and int(choice) < 3):
                choice = int(choice)
                ask_again = False

            if ask_again:
                print("\033[0;33mInvalid choice\033[0;0m")
        
        vote = choice == 1
        
        cookies = self.get_cookies(self.max_generations)

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        print("Please wait... \n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = [executor.submit(self.send_game_vote, game_id, vote, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                    req_sent += 1
                except Exception as e:
                    is_success, response_text = False, str(e)
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "New votes")

    @Utils.retry_on_exception
    def send_game_vote(self, game_id, vote, cookie):
        proxies = self.get_random_proxies() if self.use_proxy else None
        user_agent = self.get_random_user_agent()
        csrf_token = self.get_csrf_token(proxies, cookie)

        req_url = f"https://www.roblox.com/voting/vote?assetId={game_id}&vote={'true' if vote else 'false'}"
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "X-Csrf-Token": csrf_token, "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

        response = requests.post(req_url, headers=req_headers, cookies=req_cookies, proxies=proxies)
    
        return (response.status_code == 200 and response.json()["Success"]), response.text