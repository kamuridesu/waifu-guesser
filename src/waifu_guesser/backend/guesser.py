from base64 import b64decode
from io import BytesIO
import json
import aiohttp
from Shimarin.client.events import Event, EventsHandlers, EventPolling

from waifu_guesser.backend.config import AUTOTAGGER_URL, PASSWORD, SERVER_ENDPOINT, USERNAME


ev = EventsHandlers()


async def get_tags(payload: dict[str, str]):
    tags = []
    file = b64decode(payload.get("image", ""))
    async with aiohttp.ClientSession() as client:
        data = aiohttp.FormData()
        data.add_field("file", BytesIO(file), filename="test.jpg", content_type="image/jpeg")
        data.add_field("format", str(payload.get("format", "html")))
        data.add_field("limit", str(payload.get("limit", 50)))
        data.add_field("threshold", str(payload.get("threshold", 0.1)))
        async with client.post(AUTOTAGGER_URL +"/evaluate", data=data) as response:
            if response.content_type.lower() == "application/json":
                d = await response.json()
                if isinstance(d, dict) and d.get("error") != None:
                    print(d["message"])
                    return tags
                for name, rating in d[0]["tags"].items():
                    if rating > 0.5:
                        tags.append(name)
            return tags


@ev.new("danbooru_new_image")
async def handle_new_image(event: Event):
    if event.payload is None:
        return {"ok": False, "message": "Payload is missing"}
    payload: dict[str, str] = json.loads(event.payload)
    tags = await get_tags(payload)
    await event.reply({"ok": True, "tags": tags, "content-type": payload.get("content-type", "application/json"), "image": payload.get("image", "")})

    
async def ev_poller():
    headers = {"username": USERNAME, "password": PASSWORD}
    async with EventPolling(ev) as poller:
        await poller.start(0.5, server_endpoint=SERVER_ENDPOINT, custom_headers=headers) # type: ignore
