
import asyncio
import logging
import psutil
import random
import socket

import aiohttp
from aiohttp.hdrs import ACCEPT, CONTENT_TYPE

from aioprometheus import (
    Counter,
    Gauge,
    Histogram,
    Registry,
    Service,
    Summary,
)


UPDATE_INTERVAL = 1.0


def on_timer_expiry(loop, ram_metric, cpu_metric,
                    requests_metric, payload_metric,
                    latency_metric):
    ''' Update metrics '''

    # Add ram metrics
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    ram_metric.set({'type': "virtual", }, ram.used)
    ram_metric.set({'type': "swap"}, swap.used)

    # Add cpu metrics
    for c, p in enumerate(psutil.cpu_percent(interval=1, percpu=True)):
        cpu_metric.set({'core': c}, p)

    # increment a counter
    requests_metric.inc({'path': "/"})

    payload_metric.add({'path': "/data"}, random.random() * 2**10)

    # add a random request latency
    latency_metric.add({'path': "/data"}, random.random() * 5)

    # schedule another update
    loop.call_later(
        UPDATE_INTERVAL, on_timer_expiry, loop,
        ram_metric, cpu_metric, requests_metric,
        payload_metric, latency_metric)


async def fetch_metrics(url, loop):
    ''' Fetch metrics from the service endpoint using different formats '''

    n = 3
    while n > 0:
        n -= 1

        with aiohttp.ClientSession(loop=loop) as session:
            print('fetching metrics, requesting text format')
            headers = {
                ACCEPT: 'text/plain'}
            async with session.get(url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                content_type = resp.headers.get(CONTENT_TYPE)
                print('Content-Type: {}'.format(content_type))
                print('size: {}'.format(len(content)))
                print(content.decode())

            await asyncio.sleep(1.0)

            print('fetching metrics, requesting binary format')
            headers = {
                ACCEPT: 'application/vnd.google.protobuf; '
                        'proto=io.prometheus.client.MetricFamily; '
                        'encoding=delimited'}
            async with session.get(url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                content_type = resp.headers.get(CONTENT_TYPE)
                print('Content-Type: {}'.format(content_type))
                print('size: {}'.format(len(content)))
                print(content)

            await asyncio.sleep(2.0)


def fetch_task(url, loop):
    asyncio.ensure_future(fetch_metrics(url, loop))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('aiohttp').setLevel(logging.ERROR)
    logger = logging.getLogger(__name__)

    loop = asyncio.get_event_loop()

    # create a metrics server with the default registry
    svr = Service(loop=loop)

    # Get the host name of the machine to use in metrics
    host = socket.gethostname()

    # Create our collectors
    requests_metric = Counter(
        "requests", "Number of requests.", {'host': host})
    svr.registry.register(requests_metric)

    ram_metric = Gauge(
        "memory_usage_bytes",
        "Memory usage in bytes.",
        {'host': host})
    svr.registry.register(ram_metric)
    cpu_metric = Gauge(
        "cpu_usage_percent",
        "CPU usage percent.",
        {'host': host})
    svr.registry.register(cpu_metric)

    payload_metric = Summary(
        "request_payload_size_bytes",
        "Request payload size in bytes.",
        {'host': host},
        invariants=[(0.50, 0.05), (0.99, 0.001)])
    svr.registry.register(payload_metric)

    latency_metric = Histogram(
        "request_latency_seconds", "Request latency in seconds",
        {'host': host}, buckets=[0.1, 0.5, 1.0, 5.0])
    svr.registry.register(latency_metric)

    loop.run_until_complete(svr.start())
    logger.debug('serving prometheus metrics on: %s', svr.url)

    # schedule the first update, which will continue to re-schedule itself.
    loop.call_later(
        UPDATE_INTERVAL, on_timer_expiry, loop,
        ram_metric, cpu_metric, requests_metric,
        payload_metric, latency_metric)

    # initiate the client task
    loop.call_later(1.5, fetch_task, svr.url, loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(svr.stop())
    loop.close()
