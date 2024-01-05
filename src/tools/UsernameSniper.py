import os
import concurrent.futures
import httpc
from Tool import Tool
from utils import Utils
import itertools
import click

class UsernameSniper(Tool):
    def __init__(self, app):
        super().__init__("Username Sniper", "Search for the shortest Roblox username available", app)

        self.usernames_file_path = os.path.join(self.files_directory, "usernames.txt")
        Utils.ensure_files_exist([self.usernames_file_path])

    def run(self):
        username_length = self.config["username_length"]

        if username_length < 3 or username_length > 20:
            raise Exception("Usernames can be between 3 and 20 characters long.")

        click.echo("Please be patient...it may take some time to calculate all username combinations for a given length.", fg='yellow')
        all_usernames = self.generate_usernames(username_length)

        f = open(self.usernames_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = len(all_usernames)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.check_username, username, self.config["use_proxy"]) for username in all_usernames]

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

    def generate_usernames(self, length):
        characters = 'abcdefghijklmnopqrstuvwxyz0123456789_'
        all_combinations = itertools.product(characters, repeat=length)
        usernames = [''.join(combination) for combination in all_combinations if not combination[0] == '_' and not combination[-1] == '_']
        return usernames

    @Utils.handle_exception(2)
    def check_username(self, username, use_proxy) -> tuple:
        proxies = self.get_random_proxy() if use_proxy else None

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
