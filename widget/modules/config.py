from dataclasses import dataclass
import json

CONFIG_PATH = "./config.json"


@dataclass
class Config:
    disc_enable: bool
    clock_enable: bool
    ui_colors: bool
    shuffle_shortcut: str


def load_config() -> Config:
    with open(CONFIG_PATH) as file:
        data = json.load(file)
        
    return Config(
        data.get("enable_disc", True),
        data.get("enable_clock", True),
        data.get("ui_colors", True),
        data.get("shuffle_shortcut", ""),
    )
        