#!/usr/bin/env python
"""
Sometimes you want to expose Prometheus metrics from within an existing web
service and don't want to start a separate Prometheus metrics server.

This example uses the aioprometheus package to add Prometheus instrumentation
to an aiohttp application. In this example a registry and a counter metric is
instantiated. A '/metrics' route is added to the application and the render
function from aioprometheus is called to format the metrics into the
appropriate format.
"""

from aiohttp import web
from aiohttp.hdrs import ACCEPT
from aioprometheus import render, Counter, Registry


app = web.Application()
app.registry = Registry()
app.events_counter = Counter("events", "Number of events.")
app.registry.register(app.events_counter)


async def handle_root(request):
    app.events_counter.inc({"path": "/"})
    text = "Hello aiohttp"
    return web.Response(text=text)


async def handle_metrics(request):
    content, http_headers = render(app.registry, request.headers.getall(ACCEPT, []))
    return web.Response(body=content, headers=http_headers)


app.add_routes([web.get("/", handle_root), web.get("/metrics", handle_metrics)])


web.run_app(app)
