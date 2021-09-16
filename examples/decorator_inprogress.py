#!/usr/bin/env python
"""

.. code-block:: python

    $ python decorator_inprogress.py

The example script can be tested using ``curl``.

.. code-block:: console

    $ curl :8000/metrics
    # HELP request_in_progress Number of requests in progress
    # TYPE request_in_progress gauge
    request_in_progress{route="/"} 1

"""

import asyncio
import random

from aioprometheus import Counter, Gauge, inprogress
from aioprometheus.service import Service

# Create a metric to track requests currently in progress.
REQUESTS_IN_PROGRESS = Gauge("request_in_progress", "Number of requests in progress")
REQUESTS = Counter("request_total", "Total number of requests")

# Decorate function with metric.
@inprogress(REQUESTS_IN_PROGRESS, {"route": "/"})
async def handle_request(duration):
    """A dummy function that takes some time"""
    REQUESTS.inc({"route": "/"})
    await asyncio.sleep(duration)


async def handle_requests():
    # Start up the server to expose the metrics.
    await svr.start(port=8000)
    # Generate some requests.
    while True:
        await handle_request(random.random())


if __name__ == "__main__":

    loop = asyncio.get_event_loop()

    svr = Service()

    try:
        loop.run_until_complete(handle_requests())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.stop()
    loop.close()
