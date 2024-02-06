import os
import concurrent.futures
import httpc
from Tool import Tool
from utils import Utils
import random

class UsernameSniper(Tool):
    def __init__(self, app):
        super().__init__("Username Sniper", "Search for the shortest Roblox username available", app)

        self.usernames_file_path = os.path.join(self.files_directory, "usernames.txt")
        Utils.ensure_files_exist([self.usernames_file_path])

    def run(self):
        username_length = self.config["username_length"]
        max_generations = self.config["max_generations"]

        if username_length < 3 or username_length > 20:
            raise Exception("Usernames can be between 3 and 20 characters long.")

        f = open(self.usernames_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = max_generations

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.check_username, self.config["username_length"], self.config["use_proxy"]) for gen in range(max_generations)]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue

                try:
                    is_available, username, response_text = future.result()
                except Exception as e:
                    is_available, response_text = False, str(e)

                if is_available:
                    worked_gen += 1
                    f.write(username+"\n")
                    f.flush()
                else:
                    failed_gen += 1

                self.print_status(worked_gen, failed_gen, total_gen, response_text, is_available, "Available")
        f.close()

    def generate_random_username(self, length):
        characters = 'abcdefghijklmnopqrstuvwxyz0123456789_'
        username = ''.join(random.choice(characters) for _ in range(length))

        while username[0] == '_' or username[-1] == '_' or username.count('_') > 1:
            username = ''.join(random.choice(characters) for _ in range(length))

        return username

    @Utils.handle_exception(2)
    def check_username(self, username_length, use_proxy) -> tuple:
        proxies = self.get_random_proxy() if use_proxy else None

        username = self.generate_random_username(username_length)

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            csrf_token = self.get_csrf_token(None, client)

            req_headers = httpc.get_roblox_headers(user_agent, csrf_token)
            req_url = "https://auth.roblox.com/v1/usernames/validate"
            req_json = {
                "username": username,
                "context": "Signup",
                "birthday": "1999-01-01T05:00:00.000Z"
            }

            result = client.post(req_url, headers=req_headers, json=req_json)

        is_available = "Username is valid" in result.text

        return is_available, username, f"{username} {result.text}"
