from Tool import Tool
import os
import requests
import ipaddress
import concurrent.futures

class ProxyChecker(Tool):
    def __init__(self, app):
        super().__init__("Proxy Checker", "Checks proxies from a list of HTTP and SOCKS proxies", 1, app)

        self.file_path = self.app.proxies_file_path
        self.cache_file_path = os.path.join(self.cache_directory, "verified-proxies.txt")
    
    def run(self):
        delete_proxies = self.config["delete_failed_proxies"]
        timeout = self.config["timeout"]
        max_workers = self.config["max_workers"]

        # make sure format of the file is good
        try:
            self.check_proxies_file_format(self.file_path, False)
        except SyntaxError as e:
            print("\033[1;31m" + str(e) + "\033[0;0m")
            return
        except FileNotFoundError as e:
            print("\033[1;31m" + str(e) + "\033[0;0m")
            return
        except Exception as e:
            print("\033[1;31m" + str(e) + "\033[0;0m")
            return
             
        # open files/proxies.txt file
        f = open(self.file_path, 'r+')
        
        # get file lines
        lines = f.read().splitlines()
        # remove duplicates
        lines = [*set(lines)]

        f.close()
        f = open(self.cache_file_path, 'w')
        f.seek(0)
        f.truncate()
        
        working_proxies = 0
        failed_proxies = 0
        total_proxies = len(lines)

        print("Please wait... \n ")

        # for each line, test the proxy
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = [executor.submit(self.test_proxy_line, line, timeout) for line in lines]

            for future in concurrent.futures.as_completed(results):
                is_working, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = future.result()

                if is_working:
                    working_proxies += 1
                else:
                    failed_proxies += 1
                
                line = self.write_proxy_line(proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass)

                if not (delete_proxies and not is_working):
                    f.write(line + "\n") 

                print("\033[1A\033[K\033[1A\033[K\033[1;32mWorking: "+str(working_proxies)+"\033[0;0m | \033[1;31mFailed: "+str(failed_proxies)+"\033[0;0m | \033[1;34mTotal: "+str(total_proxies) + "\033[0;0m")
                print("\033[1;32mWorked: " + line + "\033[0;0m" if is_working else "\033[1;31mFailed: " + line + "\033[0;0m")          

        f.close()
        os.replace(self.cache_file_path, self.file_path)

    def test_proxy_line(self, line: str, timeout: int) -> bool:
        """
        Checks if a line proxy is working
        """

        line = self.clear_line(line)
        try:
            proxy_type_provided, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.get_proxy_values(line)
        except ValueError as e:
            print("\033[1;31m" + str(e) + "\033[0;0m")
            return

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
        
    def test_proxy(self, proxies: dict, timeout:int) -> bool:
        # get client's real ip
        client_ip = requests.get('https://api.ipify.org')

        try:
            response = requests.get('https://api.ipify.org', proxies=proxies, timeout=timeout)
            proxy_real_ip = response.text
            if (proxy_real_ip == client_ip):
                return False


            response = requests.get('https://www.roblox.com', proxies=proxies, timeout=timeout)
            if (response.status_code != 200):
                return False
        except:
            return False

        return True
    
    def write_proxy_line(self, proxy_type:str, proxy_ip:str, proxy_port:int, proxy_user:str = None, proxy_pass:str = None) -> str:
        if (proxy_user is not None and proxy_pass is not None):
            auth = True
        elif (proxy_user is None and proxy_pass is None):
            auth = False
        else: 
            raise ValueError("Invalid Parameters. If proxy has auth, make sure to provide username and password")

        return f"{proxy_type + ':' if proxy_type else ''}{proxy_ip}:{proxy_port}{':' + proxy_user + ':' + proxy_pass if auth else ''}"