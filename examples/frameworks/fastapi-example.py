#!/usr/bin/env python
"""
This example adds Prometheus metrics to a FastAPI application. In this
example a counter metric is instantiated and gets updated whenever the "/"
route is accessed.

A '/metrics' route is implemented using the render function and added to
the application using the standard web framework method. The metrics route
renders Prometheus metrics from the default collector registry into the
appropriate format.

Run:

  (venv) $ pip install fastapi uvicorn
  (venv) $ python fastapi-example.py

"""

from typing import List

from fastapi import FastAPI, Header, Request, Response

from aioprometheus import REGISTRY, Counter, render

app = FastAPI()
app.state.events_counter = Counter("events", "Number of events.")


@app.get("/")
async def hello(request: Request):
    request.app.state.events_counter.inc({"path": "/"})
    return "FastAPI Hello"


@app.get("/metrics")
async def handle_metrics(
    request: Request,  # pylint: disable=unused-argument
    accept: List[str] = Header(None),
) -> Response:
    content, http_headers = render(REGISTRY, accept)
    return Response(content=content, media_type=http_headers["Content-Type"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
