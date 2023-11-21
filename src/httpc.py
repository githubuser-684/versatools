import tls_client
import random
from data.useragents import useragents

def get_random_user_agent() -> str:
    """
    Generates a random user agent
    """
    return random.choice(useragents)

def get_roblox_headers(user_agent = None, csrf_token = None, content_type = None):
    """
    Returns a dict of headers for Roblox requests
    """
    req_headers = {"Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

    if user_agent is not None:
        req_headers["User-Agent"] = user_agent

    if content_type is not None:
        req_headers["Content-Type"] = content_type

    if csrf_token is not None:
        req_headers["X-Csrf-Token"] = csrf_token

    return req_headers

def extract_cookie(response, cookie_name):
    cookie = ''.join(response.headers.get("Set-Cookie")).split(f"{cookie_name}=")[1].split(";")[0]

    return cookie

# Requests without session

def get(url, **kwargs):
    return Session().get(url, **kwargs)

def post(url, **kwargs):
    return Session().post(url, **kwargs)

class Session():
    def __init__(self, **kwargs):
        self.session = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True,
        )
        self.session.proxies = kwargs.get("proxies")

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def get(self, url, **kwargs):
        return self._make_request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._make_request("POST", url, **kwargs)

    def _make_request(self, method, url, **kwargs):
        proxies = kwargs.get("proxies")
        headers = kwargs.get("headers")
        cookies = kwargs.get("cookies")
        json_data = kwargs.get("json")
        data = kwargs.get("data")
        params = kwargs.get("params")

        if method == "GET":
            response = self.session.get(url, proxy=proxies, headers=headers, cookies=cookies, json=json_data, data=data, params=params)
        elif method == "POST":
            response = self.session.post(url, proxy=proxies, headers=headers, cookies=cookies, json=json_data, data=data, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # add original request to the returned
        response.request = kwargs
        response.request["method"] = method
        response.request["url"] = url

        return response