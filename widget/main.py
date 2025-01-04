from connection import start_server
import ui

ui.clear_screen()
ui.hide_cursor()

start_server()

ui.error_message("no source")
