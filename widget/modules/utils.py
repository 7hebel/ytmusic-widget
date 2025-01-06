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
    