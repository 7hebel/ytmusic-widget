from modules import utils
from modules import ui

from typing import Callable
import threading
import time
import math


class Ticker:
    def __init__(self, max_step: int, frame_duration_s: float, seq_cooldown_s: float, on_tick: Callable) -> None:
        self.max_step = max_step
        self.frame_duration_s = frame_duration_s
        self.seq_cooldown_s = seq_cooldown_s
        self.on_tick = on_tick

        self.__step = 0
        self.__paused = False
        self.__ticker_abort_sig = False
        self.__ticker = threading.Thread(target=self.ticker, daemon=True)

        self.start()

    @property
    def step(self) -> int:
        return self.__step

    def __tick(self) -> None:
        self.on_tick()

        self.__step += 1
        if self.__step > self.max_step:
            self.__step = 0
            time.sleep(self.seq_cooldown_s)

    def ticker(self) -> None:
        while 1:
            if self.__ticker_abort_sig:
                self.__ticker_abort_sig = False
                return

            if self.__paused:
                continue

            time.sleep(self.frame_duration_s)

            self.__tick()

    def reset(self) -> None:
        self.__ticker_abort_sig = True
        self.__paused = True
        self.__step = 0
        self.__ticker = threading.Thread(target=self.ticker, daemon=True)

    def start(self) -> None:
        self.__paused = False
        self.__ticker.start()


class DiscRenderer:
    instance: "DiscRenderer | None" = None

    def __init__(self, sizing: "ui.UiSizing") -> None:
        if DiscRenderer.instance is not None:
            raise ValueError("The singleton class DiscRenderer already has a instance.")

        self.size_factor = 0.85
        self.sizing = sizing

        self.__current_cover: "ui.Image.Image | bool" = False
        self.__disc_color_cache: dict[tuple[int, int], tuple[int, int, int]] = {}
        self.__cache_coloring()

        self.ticker = Ticker(
            max_step=60,
            frame_duration_s=0.01,
            seq_cooldown_s=5,
            on_tick=self.draw_frame
        )

        DiscRenderer.instance = self

    def __calc_shine_triangle_points(self) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        alpha_rad = math.radians(5)
        beta_rad = math.radians(self.ticker.step - 30)

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

    def __cache_coloring(self) -> None:
        self.__disc_color_cache = {}
        disc_w = self.sizing.cover_w * self.size_factor
        disc_h = self.sizing.cover_h * self.size_factor

        ellipsis = self.generate_ellipse_coordinates(disc_w, disc_h)
        lightpoint = (
            (self.sizing.cover_xy[0] + self.sizing.cover_w),
            (self.sizing.cover_xy[1] + self.sizing.cover_h)
        )

        if ui.cached_cover is None:
            avg_color = (50, 50, 50)
        else:
            avg_color = utils.get_avg_color(ui.cached_cover.resize((self.sizing.cover_h, self.sizing.cover_w)))

        for pos in ellipsis:
            distance = int(math.dist(pos, lightpoint))

            if distance > 150:
                distance = 150

            color = (
                utils.max255int(distance + avg_color[0] * (distance / 150)),
                utils.max255int(distance + avg_color[1] * (distance / 150)),
                utils.max255int(distance + avg_color[2] * (distance / 150)),
            )

            if self.__current_cover:
                disc_start_x = min(ellipsis, key=lambda x: x[0])[0]
                disc_start_y = min(ellipsis, key=lambda x: x[1])[1]
                
                x = -(pos[0] - disc_start_x) - 1
                y = pos[1] - disc_start_y

                try:
                    cover_reflection_color = self.__current_cover.getpixel((x, y))
                    color = utils.blend_colors(color, cover_reflection_color, 0.05)
                except IndexError:
                    pass
                
            self.__disc_color_cache[pos] = color

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
        self.sizing = sizing
        self.__cache_coloring()

    def on_cover_update(self, cover: "ui.Image.Image") -> None:
        self.ticker.reset()
        self.__current_cover = cover
        self.__cache_coloring()
        self.ticker.start()

    def draw_frame(self) -> None:
        if self.sizing is None or not self.__current_cover:
            return

        shine_triang = self.__calc_shine_triangle_points()

        color_positions: dict[tuple[int, int], tuple[int, int, int]] = {}
        for pos in self.generate_ellipse_coordinates(self.sizing.cover_w * self.size_factor, self.sizing.cover_h * self.size_factor):
            color = None

            if self.is_point_in_triangle(shine_triang, pos):
                distance = int(math.dist(
                    pos,
                    (self.sizing.cover_xy[0] + self.sizing.cover_w + (self.sizing.cover_w * self.size_factor / 2), 0)
                )) / 100

                if distance > 50:
                    distance = 50

                if pos in self.__disc_color_cache:
                    base_color = self.__disc_color_cache[pos]
                    color = (
                        utils.max255int(base_color[0] * 1.5 + distance),
                        utils.max255int(base_color[1] * 1.5 + distance),
                        utils.max255int(base_color[2] * 1.5 + distance),
                    )
                    color_positions[pos] = color

            else:
                color = self.__disc_color_cache.get(pos)
                color_positions[pos] = color

            if color is None:
                # This position has not been cached yet, so there is ongoing caching job caused by the screen resizing.
                # It means that part of the disc would have been drawn on the wrong position (accordingly to the old size)
                # and rest of pixels wouldn't have colors. That's why it's better not to draw this frame.
                return

        for pos, color in color_positions.items():
            if pos in self.__disc_color_cache:
                ui.write_at(ui.tcolor("█", color), pos[0], pos[1])
