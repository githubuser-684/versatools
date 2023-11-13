import httpx
from Tool import Tool
import concurrent.futures
from utils import Utils
import eel

class DisplayNameChanger(Tool):
    def __init__(self, app):
        super().__init__("Display Name Changer", "Change Display Name of your bots", 3, app)

    @Tool.handle_exit
    def run(self):
        new_display_name = self.config["new_display_name"]
        cookies = self.get_cookies()

        eel.write_terminal("\x1B[1;33mWarning: Display names can only be changed once every week\x1B[0;0m")

        req_sent = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.change_display_name, new_display_name, cookie) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "Changed")

    @Utils.handle_exception(3)
    def change_display_name(self, new_display_name, cookie):
        """
        Changes the display name of a user
        """
        proxies = self.get_random_proxies() if self.config["use_proxy"] else None

        with httpx.Client(proxies=proxies) as client:
            user_agent = self.get_random_user_agent()
            csrf_token = self.get_csrf_token(cookie, client)
            user_info = self.get_user_info(cookie, client, user_agent)
            user_id = user_info["UserID"]

            req_url = f"https://users.roblox.com/v1/users/{user_id}/display-names"
            req_cookies = {".ROBLOSECURITY": cookie}
            req_headers = self.get_roblox_headers(user_agent, csrf_token)
            req_json = {"newDisplayName": new_display_name}

            response = client.patch(req_url, headers=req_headers, cookies=req_cookies, json=req_json)

        return (response.status_code == 200), Utils.return_res(response)
