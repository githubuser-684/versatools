config = {
	"FunCaptchaSolvers": {
		"//solvers_name": ["anti-captcha", "2captcha", "capsolver", "capbypass"],
		"anti-captcha_token": "xx",
		"2captcha_token": "xx",
		"capsolver_token": "xx",
		"capbypass": "xx"
	},
	"ProxyChecker": {
		"delete_failed_proxies": True,
		"timeout": 2,
		"max_workers": None
	},
	"CookieGenerator": {
		"max_generations": 700,
		"captcha_solver": "capbypass",
		"use_proxy": True,
		"max_workers": 50
	},
	"CookieRefresher": {
		"use_proxy": True,
		"max_workers": None
	},
	"CookieChecker": {
		"delete_invalid_cookies": False,
		"use_proxy": True,
		"max_workers": None
	},
    "CookieVerifier": {
		"use_proxy": True,
		"max_workers": None
	},
	"T-ShirtGenerator": {
		"//image_search_api_url": "https://rapidapi.com/emailmatteoutile/api/image-search-api2",
		"image_search_api_key": "xx"
	},
	"MessageBot": {
		"use_proxy": True,
		"max_workers": None
	},
	"FriendRequestBot": {
		"max_generations": 20,
		"use_proxy": True,
		"max_workers": None
	},
	"StatusChanger": {
		"use_proxy": True,
		"max_workers": None
	},
	"FollowBot": {
		"max_generations": 154,
		"captcha_solver": "capbypass",
		"use_proxy": True,
		"max_workers": 50
	},
	"GameVote": {
		"max_generations": 20,
		"use_proxy": True,
		"max_workers": None
	},
	"FavoriteBot": {
		"max_generations": 10,
		"use_proxy": True,
		"max_workers": 50,
		"timeout": 0
	},
	"DisplayNameChanger": {
		"use_proxy": True,
		"max_workers": None
	},
	"GroupJoinBot": {
		"max_generations": 100,
		"captcha_solver": "capbypass",
		"use_proxy": True,
		"max_workers": 50
	},
	"AssetsDownloader": {
		"max_generations": 20,
		"use_proxy": False,
		"max_workers": None
	},
	"CommentBot": {
		"max_generations": 1,
		"captcha_solver": "capbypass",
		"use_proxy": True,
		"max_workers": 50
	},
	"Gen2018Acc": {
		"use_proxy": False
	}
}