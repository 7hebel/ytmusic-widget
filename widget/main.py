from modules import connection
from modules import config
from modules import clock
from modules import disc
from modules import ui

import keyboard


cfg = config.load_config()

ui.clear_screen()
ui.hide_cursor()


if cfg.disc_enable:
    disc.DiscRenderer(ui.calculate_sizing())
    
if cfg.clock_enable:
    clock.Clock()

if cfg.shuffle_shortcut:
    keyboard.add_hotkey(cfg.shuffle_shortcut, connection.request_shuffle)

    
connection.start_server()
