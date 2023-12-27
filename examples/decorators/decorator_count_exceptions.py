"""

Usage:

.. code-block:: python

    $ python decorator_count_exceptions.py

The example script can be tested using ``curl``.

.. code-block:: console

    $ curl localhost:8000/metrics
    # HELP request_handler_exceptions Number of exceptions in requests
    # TYPE request_handler_exceptions counter
    request_handler_exceptions{route="/"} 3

You may need to Ctrl+C twice to exit the example script.

"""

import asyncio
import random

from aioprometheus import Counter, count_exceptions
from aioprometheus.service import Service

# Create a metric to track requests currently in progress.
REQUEST_EXCEPTIONS = Counter(
    "request_handler_exceptions", "Number of exceptions in requests"
)
REQUESTS = Counter("request_total", "Total number of requests")


# Decorate function with metric.
@count_exceptions(REQUEST_EXCEPTIONS, {"route": "/"})
async def handle_request(duration):
    """A dummy function that occasionally raises an exception"""
    REQUESTS.inc({"route": "/"})
    if duration < 0.3:
        raise Exception("Ooops")
    await asyncio.sleep(duration)


async def handle_requests():
    # Generate some requests.
    while True:
        try:
            await handle_request(random.random())
        except Exception:
            pass  # keep handling


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
