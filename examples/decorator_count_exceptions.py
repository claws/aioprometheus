#!/usr/bin/env python
"""

.. code-block:: python

    $ python decorator_count_exceptions.py

The example script can be tested using ``curl``.

.. code-block:: console

    $ curl :8000/metrics
    # HELP request_handler_exceptions Number of exceptions in requests
    # TYPE request_handler_exceptions counter
    request_handler_exceptions{route="/"} 3

You may need to Ctrl+C twice to exit the example script.

"""

import asyncio
import random

from aioprometheus import Counter, Service, count_exceptions

# Create a metric to track requests currently in progress.
REQUESTS = Counter("request_handler_exceptions", "Number of exceptions in requests")


# Decorate function with metric.
@count_exceptions(REQUESTS, {"route": "/"})
async def handle_request(duration):
    """A dummy function that occasionally raises an exception"""
    if duration < 0.3:
        raise Exception("Ooops")
    await asyncio.sleep(duration)


async def handle_requests():
    # Start up the server to expose the metrics.
    await svr.start(port=8000)
    # Generate some requests.
    while True:
        try:
            await handle_request(random.random())
        except Exception:
            pass  # keep handling


if __name__ == "__main__":

    loop = asyncio.get_event_loop()

    svr = Service()
    svr.register(REQUESTS)

    try:
        loop.run_until_complete(handle_requests())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.stop()
    loop.close()
