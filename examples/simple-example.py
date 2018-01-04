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

    def on_timer_expiry(loop, events_collector):
        ''' Update the metric periodically '''
        events_collector.inc({'kind': 'timer_expiry'})
        loop.call_later(1.0, on_timer_expiry, loop, events_collector)

    loop = asyncio.get_event_loop()

    svr = Service(loop=loop)

    events_collector = Counter(
        "events",
        "Number of events.",
        const_labels={'host': socket.gethostname()})

    svr.registry.register(events_collector)

    loop.run_until_complete(svr.start(addr="127.0.0.1"))
    print('Serving prometheus metrics on: {}'.format(svr.url))

    loop.call_later(1.0, on_timer_expiry, loop, events_collector)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.close()
