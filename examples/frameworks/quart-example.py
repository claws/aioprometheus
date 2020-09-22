#!/usr/bin/env python
"""
Sometimes you may not want to expose Prometheus metrics from a dedicated
Prometheus metrics server but instead want to use an existing web framework.

This example uses the registry from the aioprometheus package to add
Prometheus instrumentation to a Quart application. In this example a registry
and a counter metric is instantiated and gets updated whenever the "/" route
is accessed. A '/metrics' route is added to the application using the standard
web framework method. The metrics route renders Prometheus  metrics into the
appropriate format.

Run:

  (venv) $ pip install quart
  (venv) $ python quart-example.py

"""

from quart import Quart, request

from aioprometheus import Counter, Registry, render

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
