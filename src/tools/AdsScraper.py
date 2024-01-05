import concurrent.futures
import httpc
import os
import re
from Tool import Tool
from utils import Utils

class AdsScraper(Tool):
    def __init__(self, app):
        super().__init__("Ads Scraper", "Scrapes ads.", app)

        self.assets_files_directory = os.path.join(self.files_directory, "./assets")
        self.ads_directory = os.path.join(self.assets_files_directory, "./ads")
        self.vertical_ads_directory = os.path.join(self.ads_directory, "./vertical")
        self.horizontal_ads_directory = os.path.join(self.ads_directory, "./horizontal")
        self.square_ads_directory = os.path.join(self.ads_directory, "./square")

        Utils.ensure_directories_exist([self.assets_files_directory, self.ads_directory, self.vertical_ads_directory, self.horizontal_ads_directory, self.square_ads_directory])

    def run(self):
        if (self.config["ad_format"] not in ["vertical", "horizontal", "square"]):
            raise Exception("Invalid ad type. Must be either \"vertical\", \"horizontal\" or \"square\"")

        worked_gen = 0
        failed_gen = 0
        total_gen = self.config["max_generations"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            self.results = [self.executor.submit(self.scrape_ad) for gen in range(self.config["max_generations"])]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue

                try:
                    has_generated, response_text = future.result()
                except Exception as e:
                    has_generated, response_text = False, str(e)

                if has_generated:
                    worked_gen += 1
                else:
                    failed_gen += 1

                self.print_status(worked_gen, failed_gen, total_gen, response_text, has_generated, "Scraped")

    @Utils.handle_exception()
    def scrape_ad(self):
        if (self.config["ad_format"] == "vertical"):
            directory = self.vertical_ads_directory
            scrape_url = "https://www.roblox.com/user-sponsorship/2"
        elif (self.config["ad_format"] == "horizontal"):
            directory = self.horizontal_ads_directory
            scrape_url = "https://www.roblox.com/user-sponsorship/1"
        elif (self.config["ad_format"] == "square"):
            directory = self.square_ads_directory
            scrape_url = "https://www.roblox.com/user-sponsorship/3"

        proxies = self.get_random_proxy() if self.config["use_proxy"] else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            headers = httpc.get_roblox_headers(user_agent)

            result = client.get(scrape_url, headers=headers)
            response = result.text

            # thanks to github.com/MyDiscordBotcom/Roblox-Ad-Scraper for the regex
            regex = '<img src=\"(.*?)\" alt=\"(.*?)\"'
            ad_img_url = re.search(regex, response).group(1)
            ad_img = client.get(ad_img_url, headers=headers).content
            ad_alt = re.search(regex, response).group(2)

            asset_path = os.path.join(directory, f"{ad_alt}.png")

            with open(asset_path, 'wb') as f:
                f.write(ad_img)

        return True, f"Scraped ad \"{ad_alt}\""