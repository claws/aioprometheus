#!/usr/bin/env python
"""
Sometimes you want to expose Prometheus metrics from within an existing web
service and don't want to start a separate Prometheus metrics server.

This example uses the aioprometheus package to add Prometheus instrumentation
to a Vibora application. In this example a registry and a counter metric is
instantiated. A '/metrics' route is added to the application and the render
function from aioprometheus is called to format the metrics into the
appropriate format.
"""

from aioprometheus import render, Counter, Registry
from vibora import Vibora, Request, Response


app = Vibora(__name__)
app.registry = Registry()
app.events_counter = Counter("events", "Number of events.")
app.registry.register(app.events_counter)


@app.route("/")
async def hello(request: Request):
    app.events_counter.inc({"path": "/"})
    return Response(b"hello")


@app.route("/metrics")
async def handle_metrics(request: Request):
    """
    Negotiate a response format by inspecting the ACCEPTS headers and selecting
    the most efficient format. Render metrics in the registry into the chosen
    format and return a response.
    """
    content, http_headers = render(app.registry, [request.headers.get("accept")])
    return Response(content, headers=http_headers)


app.run()
