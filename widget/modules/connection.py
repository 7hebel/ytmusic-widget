from modules import config
from modules import utils
from modules import ui

from enum import StrEnum
import fastapi
import asyncio
import uvicorn
import time


server = fastapi.FastAPI()
client: fastapi.WebSocket | None = None


class EventType(StrEnum):
    PLAY_STATE = "play-state"
    UPDATE_TRACK = "update-track"


@server.websocket("/")
async def handle_ws_connection(websocket: fastapi.WebSocket):
    global client
    
    await websocket.accept()
    client = websocket
    
    await request_track_update()
    
    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(data)

    except fastapi.WebSocketDisconnect:
        ui.error_message("source disconnected")


prev_call = None
async def request_track_update() -> None:
    global prev_call
    
    if client is None:
        return
    
    if prev_call is None:
        prev_call = time.time()
    elif prev_call + 5 > time.time():
        return
    
    prev_call = time.time()
    await client.send_text("reqTrack")


def request_shuffle(*_) -> None:
    if client is None:
        return
    
    asyncio.run(client.send_text("shuffle"))


async def handle_message(msg: dict) -> None:
    event = msg.get("event")
    data = msg.get("data")
    
    if event == EventType.UPDATE_TRACK:
        cover_url = data.get("cover")
        title = data.get("title")
        author = data.get("author")
        year = data.get("year")
        queue = data.get("queue")

        if not author:
            ui.error_message("no author")
            return await request_track_update()
        
        if len(year) > 4:
            year = "----"

        ui.clear_screen()

        if cover_url is not None and not cover_url.startswith("data:image"):
            cover_img = utils.get_web_image(cover_url)
            ui.render_cover(cover_img)
            
            if config.load_config().ui_colors:
                ui.UI_PRIMARY_COLOR, ui.UI_SECONDARY_COLOR = utils.prepare_ui_colors(cover_img)
            
        ui.render_metadata_line(title, author, year)
        ui.render_queue(queue)

        if ui.cached_bar:
            ui.render_time_progress(*ui.cached_bar)

    if event == EventType.PLAY_STATE:
        current = data.get("current")
        total = data.get("total")
        
        if total == "0:00":
            return
        
        ui.render_time_progress(current, total)


def start_server():
    uvicorn.run(
        server, 
        host="localhost", 
        port=50505, 
        log_level="critical"
    )
