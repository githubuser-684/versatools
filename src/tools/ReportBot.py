import httpc
from Tool import Tool
import concurrent.futures
from utils import Utils
import re

class ReportBot(Tool):
    def __init__(self, app):
        super().__init__("Report Bot", "Report massively something offending", 3, app)

        self.report_types = ["user", "game", "group"]

    @Tool.handle_exit
    def run(self):
        report_type = self.config["report_type"]
        thing_id = self.config["thing_id"]
        comment = self.config["comment"]
        use_proxy = self.config["use_proxy"]
        cookies = self.get_cookies(self.config["max_generations"])

        if report_type not in self.report_types:
            raise Exception(f"Invalid report type: {report_type}. Can only be: {self.report_types}")

        req_worked = 0
        req_failed = 0
        total_req = len(cookies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.send_report, report_type, thing_id, comment, cookie, use_proxy) for cookie in cookies]

            for future in concurrent.futures.as_completed(results):
                try:
                    has_reported, response_text = future.result()
                except Exception as e:
                    has_reported, response_text =  False, str(e)

                if has_reported:
                    req_worked += 1
                else:
                    req_failed += 1

                self.print_status(req_worked, req_failed, total_req, response_text, has_reported, "Reported")

    @Utils.handle_exception()
    def send_report(self, report_type, thing_id, comment, cookie, use_proxy):
        proxies = self.get_random_proxy() if use_proxy else None

        with httpc.Session(proxies=proxies) as client:
            user_agent = httpc.get_random_user_agent()
            verif_token = self.get_verif_token(report_type, thing_id, cookie, client, user_agent)
            req_url, redirect_url = self.get_report_url(report_type, thing_id)

            req_cookies = {
                ".ROBLOSECURITY": cookie,
            }
            req_headers = httpc.get_roblox_headers(user_agent, None, "application/x-www-form-urlencoded")
            req_data = {
                "__RequestVerificationToken": verif_token,
                "ReportCategory": "9",
                "Comment": comment,
                "Id": str(thing_id),
                "RedirectUrl": redirect_url,
                "PartyGuid": '',
                "ConversationId": ''
            }

            response = client.post(req_url, headers=req_headers, cookies=req_cookies, data=req_data)

            if response.status_code != 200:
                raise Exception(Utils.return_res(response))

            # get message <h4>here</h4>
            try:
                message = re.search(r'<div id="report-body" class="section-content">\s*<div id="report-header" class="section-header">\s*<h4>(.*?)<\/h4>', response.text).group(1)
            except AttributeError:
                return False, f"{Utils.return_res(response)} Failed to get report response."

            return True, message

    def get_report_url(self, report_type, thing_id):
        if report_type == "user":
            redirect_url = f"https://www.roblox.com/users/{thing_id}/profile"
            req_url = f"https://www.roblox.com/abusereport/userprofile?id={thing_id}&redirecturl={redirect_url}"
        elif report_type == "game":
            redirect_url = f"https://www.roblox.com/games/{thing_id}"
            req_url = f"https://www.roblox.com/abusereport/asset?id={thing_id}&redirecturl={redirect_url.replace('https://www.roblox.com', '')}"
        elif report_type == "group":
            redirect_url = f"https://www.roblox.com/groups/{thing_id}"
            req_url = f"https://www.roblox.com/abuseReport/group?id={thing_id}&RedirectUrl={redirect_url}"
        else:
            raise Exception(f"Invalid report type: {report_type}. Can only be: {self.report_types}")

        return req_url, redirect_url

    @Utils.handle_exception(2, False)
    def get_verif_token(self, report_type, thing_id, cookie, client, user_agent):
        """
        Get the verification token for a report
        """
        req_url, redirect_url = self.get_report_url(report_type, thing_id)
        req_cookies = {".ROBLOSECURITY": cookie}
        req_headers = httpc.get_roblox_headers(user_agent)

        response = client.get(req_url, headers=req_headers, cookies=req_cookies)

        if response.status_code != 200:
            raise Exception(Utils.return_res(response))

        # IN: <input name="__RequestVerificationToken" type="hidden" value="here" />
        verif_token = re.search(r'<input name="__RequestVerificationToken" type="hidden" value="(.*)" />', response.text).group(1)
        if not verif_token:
            raise Exception("Failed to get verification token")

        return verif_token
