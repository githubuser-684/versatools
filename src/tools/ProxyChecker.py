from Tool import Tool
import os
import concurrent.futures

class ProxyChecker(Tool):
    def __init__(self, app):
        super().__init__("Proxy Checker", "Checks proxies from a list of HTTP, HTTPS and SOCKS proxies", 1, app)

        self.cache_file_path = os.path.join(self.cache_directory, "verified-proxies.txt")

        self.config["delete_failed_proxies"]
        self.config["timeout"]
        self.config["max_workers"]

    def run(self):
        # make sure format of the file is good
        self.check_proxies_file_format(self.proxies_file_path)

        # get proxies lines
        f = open(self.proxies_file_path, 'r+')
        lines = f.read().splitlines()
        lines = [*set(lines)] # remove duplicates
        f.close()

        # open cache to start writing in it
        f = open(self.cache_file_path, 'w')
        f.seek(0)
        f.truncate()
        
        working_proxies = 0
        failed_proxies = 0
        total_proxies = len(lines)

        print("Please wait... \n ")

        # for each line, test the proxy
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as self.executor:
            results = [self.executor.submit(self.test_proxy_line, line, self.config["timeout"]) for line in lines]

            for future in concurrent.futures.as_completed(results):
                is_working, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = future.result()

                if is_working:
                    working_proxies += 1
                else:
                    failed_proxies += 1
                
                line = self.write_proxy_line(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)

                if not (self.config["delete_failed_proxies"] and not is_working):
                    f.write(line + "\n")
                    f.flush()

                self.print_status(working_proxies, failed_proxies, total_proxies, line, is_working, "Working")

        f.close()
        os.replace(self.cache_file_path, self.proxies_file_path)

    def test_proxy_line(self, line: str, timeout: int) -> bool:
        """
        Checks if a line proxy is working
        """

        line = self.clear_line(line)

        proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(line)

        if (proxy_type_provided):
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

        return is_working, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass