#!/usr/bin/env python
"""
Sometimes you want to expose Prometheus metrics from within an existing web
service and don't want to start a separate Prometheus metrics server.

This example uses the aioprometheus package to add Prometheus instrumentation
to a Quart application. In this example a registry and a counter metric is
instantiated. A '/metrics' route is added to the application and the render
function from aioprometheus is called to format the metrics into the
appropriate format.
"""

from aioprometheus import render, Counter, Registry
from quart import Quart, request


app = Quart(__name__)
app.registry = Registry()
app.events_counter = Counter("events", "Number of events.")
app.registry.register(app.events_counter)


@app.route("/")
async def hello():
    app.events_counter.inc({"path": "/"})
    return "hello"


@app.route("/metrics")
async def handle_metrics():
    content, http_headers = render(app.registry, request.headers.getlist("accept"))
    return content, http_headers


app.run()
