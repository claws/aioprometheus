#!/usr/bin/env python
"""
Sometimes you may not want to expose Prometheus metrics from a dedicated
Prometheus metrics server but instead want to use an existing web framework.

This example uses the registry from the aioprometheus package to add
Prometheus instrumentation to a aiohttp application. In this example a registry
and a counter metric is instantiated and gets updated whenever the "/" route
is accessed. A '/metrics' route is added to the application using the standard
web framework method. The metrics route renders Prometheus  metrics into the
appropriate format.

Run:

  (venv) $ pip install aiohttp
  (venv) $ python aiohttp-example.py

"""

from aiohttp import web
from aiohttp.hdrs import ACCEPT

from aioprometheus import Counter, Registry, render

app = web.Application()
app.registry = Registry()
app.events_counter = Counter("events", "Number of events.")
app.registry.register(app.events_counter)


async def handle_root(
    request,  # pylint: disable=unused-argument
):
    app.events_counter.inc({"path": "/"})
    text = "Hello aiohttp"
    return web.Response(text=text)


async def handle_metrics(request):
    content, http_headers = render(app.registry, request.headers.getall(ACCEPT, []))
    return web.Response(body=content, headers=http_headers)


app.add_routes([web.get("/", handle_root), web.get("/metrics", handle_metrics)])


web.run_app(app)
