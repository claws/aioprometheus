#!/usr/bin/env python
"""
This example demonstrates how aioprometheus can be used to expose metrics on
a HTTP endpoint that is provided by the aioprometheus.Service object.

.. code-block:: console

    (env) $ python simple-example.py
    Serving prometheus metrics on: http://127.0.0.1:5000/metrics

In another terminal fetch the metrics using the ``curl`` command line tool
to verify they can be retrieved by Prometheus server.
"""

import asyncio
import socket

from aioprometheus import Counter, Service

if __name__ == "__main__":

    async def main(svc: Service) -> None:

        events_counter = Counter(
            "events", "Number of events.", const_labels={"host": socket.gethostname()}
        )
        svc.register(events_counter)
        await svc.start(addr="127.0.0.1", port=5000)
        print(f"Serving prometheus metrics on: {svc.metrics_url}")

        # Now start another coroutine to periodically update a metric to
        # simulate the application making some progress.
        async def updater(c: Counter):
            while True:
                c.inc({"kind": "timer_expiry"})
                await asyncio.sleep(1.0)

        await updater(events_counter)

    loop = asyncio.get_event_loop()
    service = Service()
    try:
        loop.run_until_complete(main(service))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(service.stop())
    loop.close()
