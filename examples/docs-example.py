#!/usr/bin/env python

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
        "events", "Number of events.", {'host': socket.gethostname()})

    svr.registry.register(events_collector)

    loop.run_until_complete(svr.start())
    print('serving prometheus metrics on: {}'.format(svr.url))

    loop.call_later(1.0, on_timer_expiry, loop, events_collector)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.close()
