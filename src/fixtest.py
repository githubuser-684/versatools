import httpx

req_url = "https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&minPrice=5&salesTypeFilter=1&sortAggregation=1&sortType=2&subcategory=ClassicShirts"

response = httpx.get(req_url)
result = response.text

print(result)
