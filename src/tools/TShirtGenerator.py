import os
import httpx
import random
import urllib.request
from PIL import Image
from resizeimage import resizeimage
from Tool import Tool
import eel
from utils import Utils

class TShirtGenerator(Tool):
    def __init__(self, app):
        super().__init__("T-Shirt Generator", "Generate a t-shirt from a query", 2, app)

        self.cache_img_path = os.path.join(self.cache_directory, "original-image")
        self.img_path = os.path.join(self.files_directory, "rblx-t-shirt.png")

    def run(self):
        image_search_api_key = self.config["image_search_api_key"]
        query = self.config["query"]

        # get image url
        url = "https://image-search-api2.p.rapidapi.com/image-search"

        querystring = { "q": query, "imgc": "png" }

        headers = {
        	"X-RapidAPI-Key": image_search_api_key,
        	"X-RapidAPI-Host": "image-search-api2.p.rapidapi.com"
        }

        response = httpx.get(url, headers=headers, params=querystring)

        if response.status_code == 429:
            raise Exception("Rate limited by Image Search Api. If you require more API requests, you can consider upgrading your plan here: https://rapidapi.com/emailmatteoutile/api/image-search-api2/pricing")

        if response.status_code == 403:
            raise Exception("You are not subscribed to API. Please subscribe here: https://rapidapi.com/emailmatteoutile/api/image-search-api2")

        try:
            images = response.json()["images"]
        except:
            raise Exception(f"Unable to search the image... \n\n{Utils.return_res(response)}")

        if len(images) == 0:
            raise Exception(f"No images found for query '{query}'")

        # retrieve random image from API
        image = images[random.randint(0, len(images) - 1)]
        image_src = image["src"].replace("&w=300&h=300", "")
        image_label = image["label"]
        urllib.request.urlretrieve(image_src, self.cache_img_path)

        # convert image to PNG
        img = Image.open(self.cache_img_path)
        img.save(self.cache_img_path+".png")

        # resize image
        with open(self.cache_img_path, 'r+b') as f:
            with Image.open(f) as image:
                cover = resizeimage.resize_cover(image, [585, 559], validate=False)
                cover.save(self.img_path, image.format)

        eel.write_terminal("Image label: " + image_label)
        eel.write_terminal("\x1B[0;32m" + query + " t-shirt was saved in files folder as rblx-t-shirt.png\x1B[0;0m")