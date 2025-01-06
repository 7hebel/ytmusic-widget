from modules import ui

import threading
import time
import math


class DiscRenderer:
    instance: "DiscRenderer | None" = None
    
    def __init__(self, sizing: "ui.UiSizing", animate: bool) -> None:
        if DiscRenderer.instance is not None:
            raise ValueError("The singleton class DiscRenderer already has a instance.")
        
        self.step = 0
        self.sizing = sizing
        self.size_factor = 0.85
        self.animate = animate
        
        threading.Thread(target=self.ticker, daemon=True).start()
        
        DiscRenderer.instance = self
        
    def __next_step(self) -> None:
        self.step += 1
        
        if self.step > 60:
            self.step = 0
            time.sleep(5)
        
    def ticker(self) -> None:
        while 1:
            if not self.animate:
                continue

            time.sleep(0.01)
            self.__next_step()
            self.draw_frame()
    
    def __calc_shine_triangle_points(self) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        alpha_rad = math.radians(5)
        beta_rad = math.radians(self.step - 30)
    
        p1 = (
            self.sizing.cover_xy[0] + (self.sizing.cover_w // 2),
            self.sizing.cover_xy[1] + (self.sizing.cover_h // 2)
        )
        
        p2_x = 1000 * math.cos(alpha_rad / 2)
        p2_y = 1000 * math.sin(alpha_rad / 2)
        p3_x = 1000 * math.cos(alpha_rad / 2)
        p3_y = 1000 * -math.sin(alpha_rad / 2)
    
        p2 = (
            p1[0] + (p2_x * math.cos(beta_rad) - p2_y * math.sin(beta_rad)),
            p1[1] + (p2_x * math.sin(beta_rad) + p2_y * math.cos(beta_rad))
        )
    
        p3 = (
            p1[0] + (p3_x * math.cos(beta_rad) - p3_y * math.sin(beta_rad)),
            p1[1] + (p3_x * math.sin(beta_rad) + p3_y * math.cos(beta_rad))
        )
    
        return (p1, p2, p3)
        
    def is_point_in_triangle(self, triangle: tuple[tuple[int, int]], point: tuple[int, int]) -> bool:
        (x1, y1), (x2, y2), (x3, y3) = triangle
        x, y = point
    
        denominator = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if denominator == 0:
            return False
    
        alpha = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / denominator
        beta = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / denominator
        gamma = 1 - alpha - beta
    
        return (0 <= alpha <= 1) and (0 <= beta <= 1) and (0 <= gamma <= 1)
        
    def generate_ellipse_coordinates(self, w: int, h: int, is_sub: bool = False) -> list[tuple[int, int]]:
        start_x = self.sizing.cover_xy[0] + self.sizing.cover_w
        start_y = self.sizing.cover_xy[1] + (self.sizing.cover_h // 2)
        
        coordinates = []
        rx = w / 2
        ry = h / 2 
    
        for y in range(-int(ry), int(ry) + 1):
            for x in range(0, int(rx) + 1):
                if (x**2 / rx**2) + (y**2 / ry**2) <= 1:
                    coordinates.append((start_x + x, start_y + y))

        if not is_sub:
            inner_coords = self.generate_ellipse_coordinates((w // 4), (h // 4), True)
            diff_coords = []
            
            for coord in coordinates:
                if coord not in inner_coords:
                    diff_coords.append(coord)
        
            coordinates = diff_coords
        
        return coordinates
    
    def update_sizing(self, sizing: "ui.UiSizing") -> None:
        for (x, y) in self.generate_ellipse_coordinates(self.sizing.cover_w * self.size_factor, self.sizing.cover_h * self.size_factor):
            ui.write_at(" ", x, y)
        
        self.sizing = sizing
    
    def draw_frame(self) -> None:
        if self.sizing is None:
            return
        
        shine_triang = self.__calc_shine_triangle_points()
        
        for (x, y) in self.generate_ellipse_coordinates(self.sizing.cover_w * self.size_factor, self.sizing.cover_h * self.size_factor):
            if self.is_point_in_triangle(shine_triang, (x, y)):
                color_value = 60 + 3 * int(math.dist(
                    (x, y),
                    (self.sizing.cover_xy[0] + self.sizing.cover_w + (self.sizing.cover_w * self.size_factor / 2), 0)
                ))
                
                if color_value > 255:
                    color_value = 255
                
            else:
                color_value = int(math.dist(
                    (x, y), 
                    (
                        (self.sizing.cover_xy[0] + self.sizing.cover_w),
                        (self.sizing.cover_xy[1] + self.sizing.cover_h)
                    )
                ))
                
                if color_value > 50:
                    color_value = 50
                
            color = (color_value, ) * 3
            
            ui.write_at(ui.tcolor("█", color), x, y)
            
            
        