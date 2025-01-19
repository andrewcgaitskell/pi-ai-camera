import hypercorn
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import quart_app

config = Config()
config.bind = ["0.0.0.0:5000"]

# Set timeout to a custom value (e.g., 300 seconds for 5 minutes)
config.timeout = 300

# Run the server
import asyncio
asyncio.run(serve(quart_app, config))
