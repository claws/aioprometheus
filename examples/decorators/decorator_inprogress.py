"""

Usage:

.. code-block:: python

    $ python decorator_inprogress.py

The example script can be tested using ``curl``.

.. code-block:: console

    $ curl localhost:8000/metrics
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
    # Generate some requests.
    while True:
        # Perform two requests to increase likelihood of observing two
        # requests in progress when fetching metrics.
        await asyncio.gather(
            handle_request(random.random()),
            handle_request(random.random()),
        )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    svc = Service()

    # Start up the server to expose the metrics.
    loop.run_until_complete(svc.start(port=8000))

    try:
        loop.run_until_complete(handle_requests())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svc.stop())
    loop.stop()
    loop.close()
