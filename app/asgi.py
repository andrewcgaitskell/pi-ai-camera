import hypercorn
from hypercorn.config import Config
from hypercorn.asyncio import serve
from my_app import quart_app

config = Config()
config.bind = ["0.0.0.0:5000"]

# Run the server
import asyncio
asyncio.run(serve(quart_app, config))
