from dataclasses import dataclass
import json

CONFIG_PATH = "./config.json"


@dataclass
class Config:
    disc_enable: bool
    disc_animation: bool
    clock_enable: bool
    shuffle_shortcut: str


def load_config() -> Config:
    with open(CONFIG_PATH) as file:
        data = json.load(file)
        
    disc = data.get("disc", {})
        
    return Config(
        disc.get("enable", True),
        disc.get("animation", True),
        data.get("enable_clock", True),
        data.get("shuffle_shortcut", ""),
    )
        