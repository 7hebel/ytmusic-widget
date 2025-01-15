from modules.disc import DiscRenderer
from modules.clock import Clock
from modules import utils

from tcolorpy import tcolor, AnsiStyle
from dataclasses import dataclass
from PIL import Image
import threading
import math
import time
import sys
import os


def clear_screen():
    os.system("cls || clear")


def hide_cursor():
    print("\033[?25l", end="")


def set_cursor_pos(x: int, y: int) -> None:
    print(f"\033[{y};{x}H", end="")


def write_at(content: str, x: int, y: int) -> None:
    set_cursor_pos(x, y)
    sys.stdout.write(content + "\n")


def get_w() -> int:
    return os.get_terminal_size()[0]


def get_h() -> int:
    return os.get_terminal_size()[1]


def get_centered_cursor_start(text_len: int, output_width: int) -> int:
    return (output_width // 2) - (text_len // 2)


@dataclass
class UiSizing:
    cover_w: int
    cover_h: int
    cover_xy: tuple[int, int]
    meta_w: int
    meta_x: int
    meta_y: int
    bar_x: int
    bar_y: int
    queue_y: int


def calculate_sizing() -> UiSizing:
    cover_w = math.floor(get_w() / 3)
    cover_h = cover_w // 2
    cover_x = get_centered_cursor_start(cover_w, get_w())
    meta_y = cover_h + 3
    bar_y = meta_y + 6
    bar_x = get_centered_cursor_start(get_w() // 2, get_w())
    queue_y = get_h() - 6

    sizing = UiSizing(
        cover_w=cover_w,
        cover_h=cover_h,
        cover_xy=(cover_x, 2),
        meta_w=cover_w - 5,
        meta_x=cover_x + 2,
        meta_y=meta_y,
        bar_x=bar_x,
        bar_y=bar_y,
        queue_y=queue_y
    )

    if DiscRenderer.instance is not None:
        DiscRenderer.instance.update_sizing(sizing)

    if Clock.instance is not None:
        Clock.instance.update_position()

    return sizing


UI_PRIMARY_COLOR = (255, 255, 255)
UI_SECONDARY_COLOR = (200, 200, 200)
SIZING = calculate_sizing()

cached_cover: Image.Image | None = None
cached_title: str | None = None
cached_author: str | None = None
cached_year: str | None = None
cached_queue: list[dict[str, str]] | None = None
cached_bar: tuple[int, int] | None = None


def render_cover(image: Image.Image) -> None:
    global cached_cover
    cached_cover = image
    image = image.resize((SIZING.cover_w, SIZING.cover_h))

    if DiscRenderer.instance is not None:
        DiscRenderer.instance.on_cover_update(image)

    for y in range(0, image.size[1]):

        line = ""
        for x in range(0, image.size[0]):
            color = image.getpixel((x, y))
            line += tcolor("█", color)

        write_at(line, SIZING.cover_xy[0], SIZING.cover_xy[1] + y)


def render_time_progress(progress_info: str, total_info: str) -> None:
    global cached_bar
    cached_bar = (progress_info, total_info)

    PASSED_CHAR = "━"
    UNPASSED_CHAR = "─"

    progress_s = utils.time_to_secs(utils.parse_time(progress_info))
    total_s = utils.time_to_secs(utils.parse_time(total_info))

    perc_done = progress_s / total_s
    content = tcolor(f"{progress_info}  ", UI_SECONDARY_COLOR)

    bar_width = (get_w() // 2) - (len(progress_info) + 2) - (len(total_info)) - 1

    for i in range(bar_width):
        color = utils.blend_colors(UI_SECONDARY_COLOR, UI_PRIMARY_COLOR, (i / bar_width))
        if perc_done > (i / bar_width):
            content += tcolor(PASSED_CHAR, color)
        else:
            content += tcolor(UNPASSED_CHAR, color, styles=[AnsiStyle.DIM])

    content += tcolor(f"  {total_info}", UI_PRIMARY_COLOR)

    write_at(content, SIZING.bar_x, SIZING.bar_y)


def render_metadata_line(title: str, author: str, year: str) -> None:
    global cached_title, cached_author, cached_year
    cached_title = title
    cached_author = author
    cached_year = year

    width = SIZING.meta_w

    title_padding = get_centered_cursor_start(len(title), width) - len(author)
    year_padding = (width - 2) - (len(author) + title_padding + len(title)) - 1

    if len(author) >= title_padding + len(author):
        content = tcolor(author, UI_SECONDARY_COLOR, styles=[AnsiStyle.DIM, AnsiStyle.ITALIC])
        content += "   "
        content += tcolor(title, UI_PRIMARY_COLOR)
        content += "   "
        content += tcolor(year, UI_SECONDARY_COLOR, styles=[AnsiStyle.DIM, AnsiStyle.ITALIC])

        write_at(content, get_centered_cursor_start(utils.real_length(content), get_w()), SIZING.meta_y)

    else:
        content = tcolor(author, UI_SECONDARY_COLOR, styles=[AnsiStyle.DIM, AnsiStyle.ITALIC])
        content += (" " * title_padding)
        content += tcolor(title, UI_PRIMARY_COLOR)
        content += (" " * year_padding)
        content += tcolor(year, UI_SECONDARY_COLOR, styles=[AnsiStyle.DIM, AnsiStyle.ITALIC])

        write_at(content, SIZING.meta_x, SIZING.meta_y)


def render_queue(queue: list[dict[str, str]]) -> None:
    global cached_queue
    cached_queue = queue

    longest_title = 0
    longest_author = 0

    for item in queue:
        title = item.get("title")
        author = item.get("author")
        duration = item.get("duration")

        if len(title) > longest_title:
            longest_title = len(title)

        if len(author) > longest_author:
            longest_author = len(author)

    author_start = 3 + longest_title
    time_start = author_start + longest_author + 4
    longest_full = time_start + 8

    draw_x = get_centered_cursor_start(longest_full, get_w())

    for index, item in enumerate(queue, 1):
        title = item.get("title")
        author = item.get("author")
        duration = item.get("duration")

        color = (
            utils.max255int(UI_SECONDARY_COLOR[0] * ((len(queue) - index + 2) / (5 * len(queue))) * 3),
            utils.max255int(UI_SECONDARY_COLOR[1] * ((len(queue) - index + 2) / (5 * len(queue))) * 3),
            utils.max255int(UI_SECONDARY_COLOR[2] * ((len(queue) - index + 2) / (5 * len(queue))) * 3),
        ) #                                            ^         ^     ^                  ^
        #                         Reverse index based /          |     |                  |
        #                         Shift to the lighter spectrum /      |                  |
        #      Greater denominator decreases contrast between indexes /                   |
        #                                                            Brighten the result /

        num = tcolor(f"{index}  ", color)
        title_style = tcolor(f"{title}", color)
        author_style = tcolor(" ~ ", color) + tcolor(author, color, styles=[AnsiStyle.ITALIC, AnsiStyle.UNDERLINE])
        duration_style = tcolor(f"  ({duration})", color)

        left_len = 3 + len(title)
        author_padding = author_start - left_len
        time_padding = time_start - (left_len + author_padding + 3 + len(author))

        content = num + title_style + (" " * author_padding) + author_style + (" " * time_padding) + duration_style
        write_at(content, draw_x, SIZING.queue_y + index)


def resize_cheker() -> None:
    global SIZING

    prev_w, prev_h = get_w(), get_h()

    while 1:
        w, h = os.get_terminal_size()

        if w != prev_w or h != prev_h:
            prev_w = w
            prev_h = h

            SIZING = calculate_sizing()

            clear_screen()

            if cached_cover:
                render_cover(cached_cover)

            if cached_title:
                render_metadata_line(cached_title, cached_author, cached_year)

            if cached_queue:
                render_queue(cached_queue)

        time.sleep(0.1)


_listener = threading.Thread(target=resize_cheker, daemon=False)
_listener.start()


def error_message(content: str) -> None:
    clear_screen()

    message = tcolor("[ ", styles=[AnsiStyle.DIM]) + tcolor(content, color=(255, 0, 0), styles=[AnsiStyle.BLINK]) + tcolor(" ]", styles=[AnsiStyle.DIM])
    draw_x = get_centered_cursor_start(len(content) + 4, get_w())
    draw_y = get_h() // 2
    write_at(message, draw_x, draw_y)
