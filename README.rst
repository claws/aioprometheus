aioprometheus
=============

|ci status| |pypi| |python| |cov| |docs| |license|

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides metrics collection and serving capabilities for
use with Prometheus and compatible monitoring systems. It supports exporting
metrics into text and binary formats and pushing metrics to a gateway.

The ASGI middleware in `aioprometheus` can be used in FastAPI/Starlette and
Quart applications. `aioprometheus` can also be used in other kinds of asyncio
applications too.

The project documentation can be found on
`ReadTheDocs <http://aioprometheus.readthedocs.org/>`_.


Install
-------

.. code-block:: console

    $ pip install aioprometheus

The ASGI middleware does not have any external dependencies but the Starlette
and Quart convenience functions that handle metrics requests do.

If you plan on using the ASGI middleware in a Starlette / FastAPI application
then you can install the extra dependencies alongside `aioprometheus` by adding
extras to the install.

.. code-block:: console

    $ pip install aioprometheus[starlette]

If you plan on using the ASGI middleware in a Quart application then you can
install the extra dependencies alongside `aioprometheus` by adding extras
to the install.

.. code-block:: console

    $ pip install aioprometheus[quart]

A Prometheus Push Gateway client and a HTTP service are included, but their
dependencies are not installed by default. You can install them alongside
`aioprometheus` by adding extras to the install.

.. code-block:: console

    $ pip install aioprometheus[aiohttp]

Prometheus 2.0 removed support for the binary protocol, so in version 20.0.0 the
dependency on `prometheus-metrics-proto`, which provides binary support, is now
optional. If you need binary response support, for use with an older Prometheus,
you will need to specify the 'binary' optional extra:

.. code-block:: console

    $ pip install aioprometheus[binary]

Multiple optional dependencies can be listed at once, such as:

.. code-block:: console

    $ pip install aioprometheus[aiohttp,binary,starlette,quart]


Usage
-----

There are two basic steps involved in using aioprometheus; the first is to
instrument your software by creating metrics to monitor events and the second
is to expose the metrics to a collector.

Creating a new metric is easy. First, import the appropriate metric from
aioprometheus. In the example below it's a Counter metric. Next, instantiate
the metric with a name and a help string. Finally, update the metric when an
event occurs. In this case the counter is incremented.

.. code-block:: python

    from aioprometheus import Counter

    events_counter = Counter(
        "events_counter",
        "Total number of events.",
    )

    events_counter.inc({"kind": "event A"})

By default, metrics get registered into the default collector registry which
is available at ``aioprometheus.REGISTRY``.

A number of convenience decorator functions are included in aioprometheus that
can assist with automatically updating metrics. The ``examples`` directory
contains various decorators examples.

Once your software is instrumented with various metrics you'll want to
expose them to Prometheus or a compatible metrics collector. There are
multiple strategies available for this and the right choice depends on the
kind of thing being instrumented.

If you are instrumenting a Starlette, FastAPI or Quart application then the
easiest option for adding Prometheus metrics is to use the ASGI Middleware
provided by `aioprometheus`.

The ASGI middleware provides a default set of metrics that include counters
for total requests received, total responses sent, exceptions raised and
response status codes for route handlers.

The example below shows how to use the aioprometheus ASGI middleware in a
FastAPI application. FastAPI is built upon Starlette so using the middleware
in Starlette would be the same.

.. code-block:: python

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
    async def root(request: Request):
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


Other examples in the ``examples/frameworks`` directory show how aioprometheus
can be used within various web application frameworks.

The next example shows how to use the Service HTTP endpoint to provide a
dedicated metrics endpoint for other applications such as long running
distributed system processes.

.. code-block:: python

    #!/usr/bin/env python
    """
    This example demonstrates how the ``aioprometheus.Service`` can be used to
    expose metrics on a HTTP endpoint.

    .. code-block:: console

        (env) $ python simple-service-example.py
        Serving prometheus metrics on: http://127.0.0.1:8000/metrics

    You can open the URL in a browser or use the ``curl`` command line tool to
    fetch metrics manually to verify they can be retrieved by Prometheus server.

    """

    import asyncio
    import socket

    from aioprometheus import Counter
    from aioprometheus.service import Service


    async def main():

        service = Service()
        events_counter = Counter(
            "events", "Number of events.", const_labels={"host": socket.gethostname()}
        )

        await service.start(addr="127.0.0.1", port=8000)
        print(f"Serving prometheus metrics on: {service.metrics_url}")

        # Now start another coroutine to periodically update a metric to
        # simulate the application making some progress.
        async def updater(c: Counter):
            while True:
                c.inc({"kind": "timer_expiry"})
                await asyncio.sleep(1.0)

        await updater(events_counter)

        # Finally stop server
        await service.stop()


    if __name__ == "__main__":

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pass

A counter metric is used to track the number of while loop iterations executed
by the 'updater' coroutine. The Service is started and then a coroutine is
started to periodically update the metric to simulate progress.

The Service can be configured to bind to a user defined network interface and
port.

When the Service receives a request for metrics it forms a response by
rendering the contents of its registry into the appropriate format. By default
the Service uses the default collector registry, which is
``aioprometheus.REGISTRY``. The Service can be configured to use a different
registry by passing one in as an argument to the Service constructor.

The Service object requires optional extras to be installed so make sure you
install aioprometheus with the 'aiohttp' extras.

.. code-block:: console

    $ pip install aioprometheus[aiohttp]


License
-------

`aioprometheus` is released under the MIT license.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package which
was released under the MIT license. `aioprometheus` continues to use the MIT
license and contains a copy of the original MIT license from the
`prometheus-python` project as instructed by the original license.


.. |ci status| image:: https://github.com/claws/aioprometheus/workflows/CI%20Pipeline/badge.svg?branch=master
    :target: https://github.com/claws/aioprometheus/actions?query=branch%3Amaster

.. |pypi| image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

.. |python| image:: https://img.shields.io/pypi/pyversions/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus/

.. |cov| image:: https://codecov.io/github/claws/aioprometheus/branch/master/graph/badge.svg?token=oPPBg8hBgc
    :target: https://codecov.io/github/claws/aioprometheus

.. |docs| image:: https://readthedocs.org/projects/aioprometheus/badge/?version=latest
    :target: https://aioprometheus.readthedocs.io/en/latest

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://github.com/claws/aioprometheus/License/LICENSE
