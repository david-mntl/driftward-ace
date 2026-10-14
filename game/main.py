# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///
"""Entry point: start the async game loop."""

import asyncio

from app.loop import run

asyncio.run(run())
