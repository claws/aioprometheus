#!/usr/bin/env python
"""
This script implements a fetching function that emulates Prometheus server
scraping a metrics service endpoint. The fetching function can randomly
requests metrics in text or binary formats or you can specify a format to
use.


Usage:

    $ python metrics-fetcher.py --url http://0.0.0.0:50123/metrics --format=text --interval=2.0

"""

import argparse
import asyncio
import logging
import random

import aiohttp
import prometheus_metrics_proto
from aiohttp.hdrs import ACCEPT, CONTENT_TYPE

import aioprometheus

TEXT = "text"
BINARY = "binary"
header_kinds = {
    TEXT: aioprometheus.formats.text.TEXT_CONTENT_TYPE,
    BINARY: aioprometheus.formats.binary.BINARY_CONTENT_TYPE,
}


async def fetch_metrics(
    url: str,
    fmt: str = None,
    interval: float = 1.0,
):
    """Fetch metrics from the service endpoint using different formats.

    This coroutine runs 'n' times, with a brief interval in between, before
    exiting.
    """
    if fmt is None:
        # Randomly choose a format to request metrics in.
        choice = random.choice((TEXT, BINARY))
    else:
        assert fmt in header_kinds
        choice = fmt

    print(f"fetching metrics in {choice} format")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={ACCEPT: header_kinds[choice]}) as resp:
            assert resp.status == 200
            content = await resp.read()
            content_type = resp.headers.get(CONTENT_TYPE)
            print(f"Content-Type: {content_type}")
            print(f"size: {len(content)}")
            if choice == "text":
                print(content.decode())
            else:
                print(content)
                # Decode the binary metrics into protobuf objects
                print(prometheus_metrics_proto.decode(content))

    # schedule another fetch
    asyncio.get_event_loop().call_later(interval, fetch_task, url, fmt, interval)


def fetch_task(url, fmt, interval):
    asyncio.ensure_future(fetch_metrics(url, fmt, interval))


if __name__ == "__main__":

    ARGS = argparse.ArgumentParser(description="Metrics Fetcher")
    ARGS.add_argument("--url", type=str, default=None, help="The metrics URL")
    ARGS.add_argument(
        "--format",
        type=str,
        default=None,
        help="Metrics response format (i.e. 'text' or 'binary'",
    )
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

    loop = asyncio.get_event_loop()

    # create a task to fetch metrics at a periodic interval
    loop.call_later(args.interval, fetch_task, args.url, args.format, args.interval)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    loop.stop()
    loop.close()
