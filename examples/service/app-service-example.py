"""
This example implements an application that exposes application metrics
obtained from the psutil package.

This example requires the ``psutil`` package which can be installed
using ``pip install psutil``.
"""

import asyncio
import logging
import random
import socket

import psutil

from aioprometheus import Counter, Gauge, Histogram, Summary
from aioprometheus.service import Service


class ExampleApp:
    """
    This example application attempts to demonstrates how ``aioprometheus``
    can be integrated within a Python application built upon asyncio.

    This application attempts to simulate a long running distributed system
    process. It is intentionally not a web service application.

    In this case the aioprometheus Service object is used to provide a
    new HTTP endpoint that can be used to expose Prometheus metrics on.
    """

    def __init__(
        self,
        metrics_host="127.0.0.1",
        metrics_port: int = 8000,
    ):
        self.metrics_host = metrics_host
        self.metrics_port = metrics_port
        self.timer = None  # type: asyncio.Handle

        ######################################################################
        # Create application metrics and metrics service

        # Create a metrics server. The server will create a metrics collector
        # registry if one is not specifically created and passed in.
        self.msvr = Service()

        # Define some constant labels that need to be added to all metrics
        const_labels = {
            "host": socket.gethostname(),
            "app": f"{self.__class__.__name__}",
        }

        # Create metrics collectors. No registry is passed when creating the
        # metrics so they get registered with the default registry.

        # Create a counter metric to track requests.
        self.requests_metric = Counter(
            "requests", "Number of requests.", const_labels=const_labels
        )

        # Create a gauge metrics to track memory usage.
        self.ram_metric = Gauge(
            "memory_usage_bytes", "Memory usage in bytes.", const_labels=const_labels
        )

        # Create a gauge metrics to track CPU.
        self.cpu_metric = Gauge(
            "cpu_usage_percent", "CPU usage percent.", const_labels=const_labels
        )

        self.payload_metric = Summary(
            "request_payload_size_bytes",
            "Request payload size in bytes.",
            const_labels=const_labels,
            invariants=[(0.50, 0.05), (0.99, 0.001)],
        )

        self.latency_metric = Histogram(
            "request_latency_seconds",
            "Request latency in seconds",
            const_labels=const_labels,
            buckets=[0.1, 0.5, 1.0, 5.0],
        )

    async def start(self):
        """Start the application"""
        await self.msvr.start(addr=self.metrics_host, port=self.metrics_port)
        logger.debug(f"Serving prometheus metrics on: {self.msvr.metrics_url}")

        # Schedule a timer to update metrics. In a realistic application
        # the metrics would be updated as needed. In this example, a simple
        # timer is used to emulate things happening, which conveniently
        # allows all metrics to be updated at once.
        self.timer = asyncio.get_event_loop().call_later(1.0, self.on_timer_expiry)

    async def stop(self):
        """Stop the application"""
        await self.msvr.stop()
        if self.timer:
            self.timer.cancel()
        self.timer = None

    def on_timer_expiry(self):
        """Update application to simulate work"""

        # Update memory metrics
        self.ram_metric.set({"type": "virtual"}, psutil.virtual_memory().used)
        self.ram_metric.set({"type": "swap"}, psutil.swap_memory().used)

        # Update cpu metrics
        for c, p in enumerate(psutil.cpu_percent(interval=1, percpu=True)):
            self.cpu_metric.set({"core": c}, p)

        # Incrementing a requests counter to emulate webserver app
        self.requests_metric.inc({"path": "/"})

        # Monitor request payload data to emulate webserver app
        self.payload_metric.add({"path": "/data"}, random.random() * 2**10)

        # Monitor request latency to emulate webserver app
        self.latency_metric.add({"path": "/data"}, random.random() * 5)

        # re-schedule another metrics update
        self.timer = asyncio.get_event_loop().call_later(1.0, self.on_timer_expiry)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Silence asyncio and aiohttp loggers
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)
    logger = logging.getLogger(__name__)

    loop = asyncio.get_event_loop()

    app = ExampleApp()

    loop.run_until_complete(app.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app.stop())
    loop.close()
