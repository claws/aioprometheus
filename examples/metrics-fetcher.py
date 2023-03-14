"""
This script implements a fetching function that emulates a Prometheus server
scraping a metrics service endpoint.

This script requires some optional extras to be installed.

.. code-block:: console

    $ pip install aioprometheus[aiohttp]

Usage:

.. code-block:: console

    $ python metrics-fetcher.py --url http://0.0.0.0:50123/metrics --interval=2.0

"""

import argparse
import asyncio
import logging

import aiohttp
from aiohttp.hdrs import ACCEPT, CONTENT_TYPE

from aioprometheus import formats


async def fetch_metrics(
    url: str,
    interval: float = 1.0,
):
    """Fetch metrics from the service endpoint.

    This coroutine runs forever, with a brief interval in between calls.
    """
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                print("Fetching metrics")
                async with session.get(
                    url, headers={ACCEPT: formats.text.TEXT_CONTENT_TYPE}
                ) as resp:
                    assert resp.status == 200
                    content = await resp.read()
                    content_type = resp.headers.get(CONTENT_TYPE)
                    print(f"Content-Type: {content_type}, size: {len(content)}")
                    print(content.decode())
                    print("")

                # Wait briefly before fetching again
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                return


if __name__ == "__main__":
    ARGS = argparse.ArgumentParser(description="Metrics Fetcher")
    ARGS.add_argument("--url", type=str, default=None, help="The metrics URL")
    ARGS.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="The number of seconds between metrics requests",
    )
    ARGS.add_argument(
        "--debug", default=False, action="store_true", help="Show debug output"
    )

    args = ARGS.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        # Silence asyncio and aiohttp loggers
        logging.getLogger("asyncio").setLevel(logging.ERROR)
        logging.getLogger("aiohttp").setLevel(logging.ERROR)

    try:
        asyncio.run(fetch_metrics(args.url, args.interval))
    except KeyboardInterrupt:
        pass
