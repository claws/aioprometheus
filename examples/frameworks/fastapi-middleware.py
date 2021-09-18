#!/usr/bin/env python
"""
This example shows how to use the aioprometheus ASGI middleware in a FastAPI
application. FastAPI is built upon Starlette so using the middleware in
Starlette would be the same.

Run:

  (venv) $ pip install fastapi uvicorn
  (venv) $ python fastapi-middleware.py

"""

from fastapi import FastAPI, Request, Response

from aioprometheus import Counter, MetricsMiddleware
from aioprometheus.asgi.starlette import metrics

app = FastAPI()

# Any custom application metrics are automatically included in the exposed
# metrics. It is a good idea to attach the metrics to 'app.state' so they
# can easily be accessed in the route handler - as metrics are often
# created in a different module than where they are used.
app.state.users_events_counter = Counter("events", "Number of events.")

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics)


@app.get("/")
async def root(request: Request):  # pylint: disable=unused-argument
    return Response("FastAPI Middleware Example")


@app.get("/users/{user_id}")
async def get_user(
    request: Request,
    user_id: str,
):
    request.app.state.users_events_counter.inc({"path": request.scope["path"]})
    return Response(f"{user_id}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
