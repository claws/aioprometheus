#!/usr/bin/env python
"""
Usage:

.. code-block:: python

    $ python decorator_timer.py

The example script can be tested using ``curl``.

.. code-block:: console

    $ curl :8000/metrics
    # HELP request_processing_seconds Time spent processing request
    # TYPE request_processing_seconds summary
    request_processing_seconds_count 77
    request_processing_seconds_sum 38.19072341918945
    request_processing_seconds{quantile="0.5"} 0.27150511741638184
    request_processing_seconds{quantile="0.9"} 0.5016570091247559
    request_processing_seconds{quantile="0.99"} 0.6077709197998047

"""

import asyncio
import random

from aioprometheus import Service, Summary, timer

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing request")


# Decorate function with metric.
@timer(REQUEST_TIME)
async def handle_request(duration):
    """A dummy function that takes some time"""
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
    svr.register(REQUEST_TIME)

    try:
        loop.run_until_complete(handle_requests())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.stop()
    loop.close()
