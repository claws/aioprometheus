#!/usr/bin/env python
'''
This example demonstrates how a single Counter metric collector can be created
and exposed via a HTTP endpoint.

.. code-block:: console

    (env) $ python simple-example.py
    Serving prometheus metrics on: http://127.0.0.1:50624/metrics

In another terminal fetch the metrics using the ``curl`` command line tool
to verify they can be retrieved by Prometheus server.
'''
import asyncio
import socket
from aioprometheus import Counter, Service


if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    svr = Service()

    events_counter = Counter(
        "events",
        "Number of events.",
        const_labels={'host': socket.gethostname()})

    svr.register(events_counter)

    loop.run_until_complete(svr.start(addr="127.0.0.1"))
    print(f'Serving prometheus metrics on: {svr.metrics_url}')

    async def updater(m: Counter):
        # Periodically update the metric to simulate some progress
        # happening in a real application.
        while True:
            m.inc({'kind': 'timer_expiry'})
            await asyncio.sleep(1.0)

    try:
        loop.run_until_complete(updater(events_counter))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.close()
