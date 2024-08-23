import os
import uvloop
from waifu_guesser.frontend.app import app
from src.waifu_guesser.backend.guesser import ev_poller


async def frontend():
    from hypercorn import Config
    from hypercorn.asyncio import serve

    SERVER_PORT = os.getenv("SERVER_PORT", 16045)
    
    config = Config()
    # config.accesslog = "-"
    config.errorlog = "-"
    config.bind = f"0.0.0.0:{SERVER_PORT}"

    await serve(app, config)


async def backend():
    await ev_poller()


async def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "back":
        return await backend()
    return await frontend()

if __name__ == "__main__":
    uvloop.run(main())

