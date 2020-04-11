#!/usr/bin/env python
"""
Sometimes you may not want to expose Prometheus metrics from a dedicated
Prometheus metrics server but instead want to use an existing web framework.

This example uses the registry from the aioprometheus package to add
Prometheus instrumentation to a FastAPI application. In this example a registry
and a counter metric is instantiated and gets updated whenever the "/" route
is accessed. A '/metrics' route is added to the application using the standard
web framework method. The metrics route renders Prometheus metrics into the
appropriate format.

Run:

  (venv) $ pip install fastapi uvicorn
  (venv) $ uvicorn fastapi_example:app

"""

from aioprometheus import render, Counter, Registry
from fastapi import FastAPI, Header, Response
from typing import List


app = FastAPI()
app.registry = Registry()
app.events_counter = Counter("events", "Number of events.")
app.registry.register(app.events_counter)


@app.get("/")
async def hello():
    app.events_counter.inc({"path": "/"})
    return "hello"


@app.get("/metrics")
async def handle_metrics(response: Response, accept: List[str] = Header(None)):
    content, http_headers = render(app.registry, accept)
    return Response(content=content, media_type=http_headers["Content-Type"])
