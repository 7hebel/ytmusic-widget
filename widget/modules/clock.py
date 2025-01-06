from modules import ui

import threading
import time


class Clock:
    instance: "Clock | None" = None
    
    def __init__(self) -> None:
        if Clock.instance is not None:
            raise ValueError("The singleton class Clock already has a instance.")
            
        self.y = ui.get_h() - 1
        self.x = ui.get_w() - 5
        Clock.instance = self
        
        threading.Thread(target=self.ticker, daemon=True).start()

    def get_time(self) -> str:
        return time.strftime("%H:%M")
        
    
    def update_position(self) -> None:
        ui.write_at("     ", self.x, self.y)
        self.y = ui.get_h() - 1
        self.x = ui.get_w() - 5

    def ticker(self) -> None:
        while 1:
            time.sleep(1)
            curr_time = self.get_time()
            ui.write_at(ui.tcolor(curr_time, styles=[ui.AnsiStyle.DIM, ui.AnsiStyle.ITALIC]), self.x, self.y)
