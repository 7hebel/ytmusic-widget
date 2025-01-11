from functools import lru_cache
from io import BytesIO
from PIL import Image
import requests
import re


def real_length(styled_text: str) -> int:
    """ Returns length of ANSI-escaped string. """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    plain_text = ansi_escape.sub('', styled_text)
    return len(plain_text)
   
    
def parse_time(time_info: str) -> float:
    """ 12:45 -> 12.45 """
    return float(time_info.replace(":", "."))
   
   
def time_to_secs(time: float) -> int:
    """ 1.34 -> 94 """
    mins, secs = str(time).split(".")
    if len(secs) == 1:
        secs = int(secs) * 10
    
    secs = int(secs) + (60 * int(mins))
    return secs
 
    
def get_web_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=3)
    return Image.open(BytesIO(resp.content))
    

Image.Image.__hash__ = lambda self: hash(str(list(self.getdata())))

@lru_cache
def get_avg_color(im: Image.Image) -> tuple[int, int, int]:
    image = im.convert("RGB")
    pixels = list(image.getdata())
    
    total_pixels = len(pixels)
    avg_r = sum(pixel[0] for pixel in pixels) / total_pixels
    avg_g = sum(pixel[1] for pixel in pixels) / total_pixels
    avg_b = sum(pixel[2] for pixel in pixels) / total_pixels
    
    return  (int(avg_r), int(avg_g), int(avg_b))
    
    