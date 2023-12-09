import re
import httpc
from Tool import Tool
from utils import Utils
import concurrent.futures

class VipServerScraper(Tool):
    def __init__(self, app):
        super().__init__("Vip Server Scraper", "Scrape Roblox VIP servers", 3, app)

    @Tool.handle_exit
    def run(self):
        max_workers = self.config["max_workers"]

        pages_game = self.get_pages_game()

        req_sent = 0
        req_failed = 0
        total_req = len(pages_game)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as self.executor:
            results = [self.executor.submit(self.get_vip_link, page_game) for page_game in pages_game]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "Scraped")

    def get_pages_game(self):
        user_agent = httpc.get_random_user_agent()
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            req_url = "https://robloxvipservers.net/servers"
            req_headers = httpc.get_roblox_headers(user_agent)

            response = client.get(req_url, headers=req_headers)

            if response.status_code != 200:
                raise Exception(Utils.return_res(response))

        # with a regex find all content inside href : href="games/920587237/Adopt+Me"
        pages = re.findall(r"href='games/(.+?)'", response.text)

        return pages

    def get_vip_link(self, page_game):
        page_id = page_game.split("/")[0]

        user_agent = httpc.get_random_user_agent()
        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            req_url = f"https://robloxvipservers.net/games/manager/{page_id}"
            req_headers = httpc.get_roblox_headers(user_agent)

            response = client.get(req_url, headers=req_headers)

        try:
            vip_link = re.findall(r'\'countdown\' href="(.+?)"', response.text)[0]
        except IndexError:
            return False, "VIP server link not found"

        return (response.status_code == 200), vip_link