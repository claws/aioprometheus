#!/usr/bin/env python
"""
This example shows how to use the aioprometheus ASGI middleware in a Quart
application.

Run:

  (venv) $ pip install quart
  (venv) $ python quart_middleware.py

"""

from quart import Quart, request

from aioprometheus import Counter, MetricsMiddleware
from aioprometheus.asgi.quart import metrics

app = Quart(__name__, static_folder=None)

# Any custom application metrics are automatically included in the exposed
# metrics. It is a good idea to attach the metrics to 'app.state' so they
# can easily be accessed in the route handler - as metrics are often
# created in a different module than where they are used.
app.users_events_counter = Counter("events", "Number of events.")

# Following Quart advice for Middleware, it is recommended to assign to and
# wrap the asgi_app attribute when adding Middleware.
app.asgi_app = MetricsMiddleware(app.asgi_app)
app.add_url_rule("/metrics", "metrics", metrics, methods=["GET"])


@app.route("/")
async def root():
    return "Quart Middleware Example"


@app.route("/users/<user_id>")
async def get_user(user_id):
    app.users_events_counter.inc({"path": request.path})
    return f"{user_id}"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
