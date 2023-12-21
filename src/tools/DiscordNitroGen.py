import os
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import httpc
from Tool import Tool
from utils import Utils
import uuid

class DiscordNitroGen(Tool):
    def __init__(self, app):
        super().__init__("Discord Nitro Gen", "Generates Nitro links from OperaGX promotion.", 5, app)

        self.nitro_file_path = os.path.join(self.files_directory, "nitros.txt")

    def run(self):
        f = open(self.nitro_file_path, 'a')

        worked_gen = 0
        failed_gen = 0
        total_gen = self.config["max_generations"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            self.results = [executor.submit(self.generate_nitro, self.config["use_proxy"]) for gen in range(self.config["max_generations"])]

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

    @Utils.handle_exception()
    def generate_nitro(self, use_proxy:bool) -> tuple:
        proxies = self.get_random_proxy() if use_proxy else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()

            req_url = "https://api.discord.gx.games/v1/direct-fulfillment"
            req_headers = {
                'Accept': '*/*',
                'Authority': 'api.discord.gx.games',
                'Accept-Language': 'en-US',
                'Origin': 'https://www.opera.com',
                'Referer': 'https://www.opera.com/',
                'Sec-ch-ua': '"Opera";v="105", "Chromium";v="119", "Not?A_Brand";v="24"',
                'Sec-ch-ua-mobile': '?0',
                'Sec-ch-ua-platform': '"Windows"',
                'Sec-fetch-dest': 'empty',
                'Sec-fetch-mode': 'cors',
                'Sec-fetch-site': 'cross-site',
                'User-Agent': user_agent,
            }
            req_json={"partnerUserId": str(uuid.uuid4())}
            result = client.post(req_url, headers=req_headers, json=req_json)

            if result.status_code != 200:
                raise Exception(Utils.return_res(result))

            response = result.json()
            token = response.get('token')

        if token == None:
            return False, "Failed to generate token. " + Utils.return_res(result)

        return True, "https://discord.com/billing/partner-promotions/1180231712274387115/"+token
