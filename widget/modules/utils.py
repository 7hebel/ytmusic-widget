from functools import lru_cache
from io import BytesIO
from PIL import Image
import colorsys
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
    

def max255int(n: int | float) -> int:
    return int(n) if n <= 255 else 255


Image.Image.__hash__ = lambda self: hash(str(list(self.getdata())))


@lru_cache
def get_avg_color(im: Image.Image) -> tuple[int, int, int]:
    image = im.convert("RGB")
    pixels = list(image.getdata())
    
    total_pixels = len(pixels)
    avg_r = sum(pixel[0] for pixel in pixels) / total_pixels
    avg_g = sum(pixel[1] for pixel in pixels) / total_pixels
    avg_b = sum(pixel[2] for pixel in pixels) / total_pixels
    
    return (int(avg_r), int(avg_g), int(avg_b))
    

def prepare_ui_color(im: Image.Image) -> list[int, int, int]:
    avg_color_rgb = get_avg_color(im)
    h, l, s = colorsys.rgb_to_hls(*[v/255 for v in avg_color_rgb])
    
    l = 0.85
    s = min(1.0, s * 1.1)
    
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def blend_colors(init_color: tuple[int, int, int], blend_color: tuple[int, int, int] | None, alpha: float) -> tuple[int, int, int]:
    if blend_color is None:
        return init_color
    
    r1, g1, b1 = init_color
    r2, g2, b2 = blend_color
    r_out = int((1 - alpha) * r1 + alpha * r2)
    g_out = int((1 - alpha) * g1 + alpha * g2)
    b_out = int((1 - alpha) * b1 + alpha * b2)
    return (r_out, g_out, b_out)
