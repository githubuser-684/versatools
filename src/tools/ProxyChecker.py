from Tool import Tool
import os
import concurrent.futures
from utils import Utils
import ipaddress
import httpc

class ProxyChecker(Tool):
    def __init__(self, app):
        super().__init__("Proxy Checker", "Checks proxies from a list of http proxies", 1, app)

        self.cache_file_path = os.path.join(self.cache_directory, "verified-proxies.txt")

    def run(self):
        # make sure format of the file is good
        self.check_proxies_file_format(self.proxies_file_path)

        # make sure ipinfo token is good
        if self.config["ipinfo_api_key"] != None and self.config["check_timezone"]:
            self.check_ipinfo_token(self.config["ipinfo_api_key"])

        # get proxies lines
        f = open(self.proxies_file_path, 'r+')
        lines = f.read().splitlines()
        lines = [*set(lines)] # remove duplicates
        f.close()

        if self.config["delete_failed_proxies"]:
            # open cache to start writing in it
            f = open(self.cache_file_path, 'w')
            f.seek(0)
            f.truncate()

        working_proxies = 0
        failed_proxies = 0
        total_proxies = len(lines)

        # for each line, test the proxy
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            self.results = [executor.submit(self.test_proxy_line, line, self.config["check_timezone"], self.config["ipinfo_api_key"], self.config["timeout"]) for line in lines]

            for future in concurrent.futures.as_completed(self.results):
                if future.cancelled():
                    continue
                is_working, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass, timezone = future.result()

                if is_working:
                    working_proxies += 1
                else:
                    failed_proxies += 1

                line = self.write_proxy_line(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)

                if self.config["delete_failed_proxies"] and is_working:
                    f.write(line + "\n")
                    f.flush()

                if timezone is not None:
                    line = f"{line} {timezone}"

                self.print_status(working_proxies, failed_proxies, total_proxies, line, is_working, "Working")

        if self.config["delete_failed_proxies"]:
            f.close()

            # replace file with cache
            with (open(self.proxies_file_path, 'w')) as f:
                f.seek(0)
                f.truncate()
                f.write(open(self.cache_file_path, 'r').read())

    def check_ipinfo_token(self, token: str):
        response = httpc.get("https://ipinfo.io/8.8.8.8?token="+token)

        if response.status_code != 200:
            error_msg = "Error from IpInfo: " + response.text
            raise Exception(error_msg)

    def test_proxy_line(self, line: str, check_timezone: bool, ipinfo_api_key:str, timeout: int):
        """
        Checks if a line proxy is working
        """

        line = Utils.clear_line(line)

        proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(line)

        if proxy_type_provided:
            proxies = self.get_proxies(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)
            is_working = self.test_proxy(proxies, timeout)
        else:
            # if protocol not specified, try all protocols...
            for protocol in self.supported_proxy_protocols:
                proxies = self.get_proxies(protocol, proxy_ip, proxy_port, proxy_user, proxy_pass)
                is_working = self.test_proxy(proxies, timeout)
                if is_working:
                    proxy_type = protocol
                    break

        timezone = None

        if is_working and check_timezone:
            api_key_param = f'?token={ipinfo_api_key}' if ipinfo_api_key else ''

            if self.ip_address_is_valid(proxy_ip):
                req_url = f'http://ipinfo.io/{proxy_ip}/json{api_key_param}'

                res = httpc.get(req_url)
            else:
                req_url = f'http://ipinfo.io/json{api_key_param}'

                res = httpc.get(req_url, proxies=proxies)

            timezone = res.json().get("timezone")

        return is_working, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass, timezone

    def ip_address_is_valid(self, ip_string):
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False