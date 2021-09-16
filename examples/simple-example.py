#!/usr/bin/env python
"""
This example demonstrates how the ``aioprometheus.Service`` can be used to
expose metrics on a HTTP endpoint.

.. code-block:: console

    (env) $ python simple-example.py
    Serving prometheus metrics on: http://127.0.0.1:8000/metrics

You can open the URL in a browser or use the ``curl`` command line tool to
fetch metrics manually to verify they can be retrieved by Prometheus server.

"""

import asyncio
import socket

from aioprometheus import Counter
from aioprometheus.service import Service


async def main():

    service = Service()
    events_counter = Counter(
        "events", "Number of events.", const_labels={"host": socket.gethostname()}
    )

    await service.start(addr="127.0.0.1", port=8000)
    print(f"Serving prometheus metrics on: {service.metrics_url}")

    # Now start another coroutine to periodically update a metric to
    # simulate the application making some progress.
    async def updater(c: Counter):
        while True:
            c.inc({"kind": "timer_expiry"})
            await asyncio.sleep(1.0)

    await updater(events_counter)

    # Finally stop server
    await service.stop()


if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
