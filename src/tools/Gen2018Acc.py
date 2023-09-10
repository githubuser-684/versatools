import httpx
from Tool import Tool
from utils import Utils
import math
import random

class Gen2018Acc(Tool):
    def __init__(self, app):
        super().__init__("Gen 2018 Acc", "2018 old roblox account generator", 6, app)

        self.config["use_proxy"]

    def run(self):
        user_id = 73223429
        default_pass = "insaneclient101"
        followers_count = self.get_followers_count(user_id)
        follower_per_page = 18
        max_pages = math.ceil(followers_count / follower_per_page)
        max_loop_pages = 50 if max_pages > 50 else max_pages
        loop_pages = random.randint(0, max_loop_pages)

        cursor = None
        followers = []
        for i in range(loop_pages):
            cursor, followers = self.get_followers(user_id, cursor, follower_per_page)

        username = followers[random.randint(0, len(followers)-1)]["name"]

        print(f"\033[1;32m2018 Account Generated: {username}:{default_pass}\033[0;0m")

    @Utils.retry_on_exception()
    def get_followers_count(self, user_id):
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()

        req_url = f"https://friends.roblox.com/v1/users/{user_id}/followers/count"
        req_headers = self.get_roblox_headers(user_agent)
        
        response = httpx.get(req_url, headers=req_headers, proxies=proxies)

        return response.json()["count"]

    @Utils.retry_on_exception()
    def get_followers(self, user_id, cursor, follower_per_page):
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None
        user_agent = self.get_random_user_agent()

        req_url = f"https://friends.roblox.com/v1/users/{user_id}/followers?sortOrder=Desc&limit={follower_per_page}{'&cursor='+cursor if cursor else ''}"
        req_headers = self.get_roblox_headers(user_agent)

        response = httpx.get(req_url, headers=req_headers, proxies=proxies)
        response_json = response.json()

        return response_json["nextPageCursor"], response_json["data"]