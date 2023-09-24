import httpx


def get_roblox_headers(user_agent, csrf_token = None, content_type = None):
    """
    Returns a dict of headers for Roblox requests
    """
    req_headers = {"User-Agent": user_agent, "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json;charset=utf-8", "Origin": "https://www.roblox.com", "Referer": "https://www.roblox.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Te": "trailers"}

    if content_type is not None:
        req_headers["Content-Type"] = content_type

    if csrf_token is not None:
        req_headers["X-Csrf-Token"] = csrf_token

    return req_headers






proxies = None
req_headers = get_roblox_headers("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")


req_url = "https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&minPrice=5&salesTypeFilter=1&sortAggregation=1&sortType=2&subcategory=ClassicShirts"



response = httpx.get(req_url, headers=req_headers, proxies=proxies)
result = response.json()

print("data found: "+ str(len(result['data'])))
