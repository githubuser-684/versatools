# Versatools

Best FREE opensource Roblox exploiting tools written in Python.

How to setup:

First clone this repository:

```bash
git clone
```

Then install the requirements:

```bash
pip install -r requirements.txt
```

Then copy paste the following config in the location `files/config.json`:

(All attributes are mandatory. Removing them will break the program.
Here are default values)

```json
{
	"FunCaptchaSolvers": {
		"//solvers_name": ["anti-captcha", "2captcha", "capsolver", "capbypass"],
		"anti-captcha_token": "xx",
		"2captcha_token": "xx",
		"capsolver_token": "xx",
		"capbypass": "xx"
	},
	"ProxyChecker": {
		"delete_failed_proxies": true,
		"timeout": 2,
		"max_workers": null
	},
	"CookieGenerator": {
		"max_generations": 700,
		"captcha_solver": "capbypass",
		"use_proxy": true,
		"max_workers": 50
	},
	"CookieRefresher": {
		"use_proxy": true,
		"max_workers": null
	},
	"CookieChecker": {
		"delete_invalid_cookies": true,
		"use_proxy": true,
		"max_workers": null
	},
	"T-ShirtGenerator": {
		"//image_search_api_url": "https://rapidapi.com/emailmatteoutile/api/image-search-api2",
		"image_search_api_key": "xx"
	},
	"MessageBot": {
		"use_proxy": true,
		"max_workers": null
	},
	"FriendRequestBot": {
		"max_generations": 20,
		"use_proxy": true,
		"max_workers": null
	},
	"StatusChanger": {
		"use_proxy": true,
		"max_workers": null
	},
	"FollowBot": {
		"max_generations": 154,
		"captcha_solver": "capbypass",
		"use_proxy": true,
		"max_workers": 50
	},
	"GameVote": {
		"max_generations": 20,
		"use_proxy": true,
		"max_workers": null
	},
	"FavoriteBot": {
		"max_generations": 10,
		"use_proxy": true,
		"max_workers": 50,
		"timeout": 0.056
	},
	"DisplayNameChanger": {
		"use_proxy": true,
		"max_workers": null
	},
	"GroupJoinBot": {
		"max_generations": 100,
		"captcha_solver": "capbypass",
		"use_proxy": true,
		"max_workers": 50
	},
	"AssetsDownloader": {
		"max_generations": 20,
		"use_proxy": false,
		"max_workers": null
	},
	"CommentBot": {
		"max_generations": 1,
		"captcha_solver": "capbypass",
		"use_proxy": true,
		"max_workers": 50
	}
}
```

Finally, run the program:

```bash
python src/main.py
```

To run unit tests:

```bash
python -m unittest discover src
```

## Template for other files

You can use this template to add your proxies. We currently support HTTP, SOCKS4 and SOCKS5 proxies.

`files/proxies.txt`

```
http:8.8.8.8:5001
socks4:8.8.8.8:5002
socks5:8.8.8.8:5003:username:password
```

or you can decide to not specify the type of proxy and let the proxy checker check it for you.

```
8.8.8.8:5001
8.8.8.8:5002
8.8.8.8:5003:username:password
```

## Contributing

If you want to contribute to this project, you can fork this repository and make a pull request. We will review it and if it is good, we will merge it.

ALL CONTRIBUTIONS ARE WELCOME!
