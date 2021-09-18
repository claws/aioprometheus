.. image:: https://github.com/claws/aioprometheus/workflows/Python%20Package%20Workflow/badge.svg?branch=master
    :target: https://github.com/claws/aioprometheus/actions?query=branch%3Amaster

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

.. image:: https://readthedocs.org/projects/aioprometheus/badge/?version=latest
    :target: https://aioprometheus.readthedocs.io/en/latest

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black

aioprometheus
=============

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides metrics collection and serving capabilities for
use with Prometheus and compatible monitoring systems. It supports exporting
metrics into text and binary formats and pushing metrics to a gateway.

`aioprometheus` can be used in applications built with FastAPI/Starlette,
Quart, aiohttp as well as networking apps built upon asyncio.

The project documentation can be found on
`ReadTheDocs <http://aioprometheus.readthedocs.org/>`_.


Install
-------

.. code-block:: console

    $ pip install aioprometheus

A Prometheus Push Gateway client and a HTTP service are included, but their
dependencies are not installed by default. You can install them alongside
`aioprometheus` by adding optional extras to the install.

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

    $ pip install aioprometheus[aiohttp,binary]


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

An example showing how aioprometheus can be used within a FastAPI app to
export metrics is shown below.

.. code-block:: python

    """
    This example uses adds some simple Prometheus instrumentation to a FastAPI
    application. In this example a counter metric is instantiated and gets
    updated whenever the "/" route is accessed. A '/metrics' route is added to
    the application using the standard web framework method. The metrics route
    renders Prometheus metrics from the default collector registry into the
    appropriate format.

    Run:

    (venv) $ pip install fastapi uvicorn
    (venv) $ python fastapi_example.py

    """

    from typing import List

    from fastapi import FastAPI, Header, Request, Response

    from aioprometheus import Counter, REGISTRY, render


    app = FastAPI()
    app.state.events_counter = Counter("events", "Number of events.")


    @app.get("/")
    async def hello(request: Request):
        request.app.state.events_counter.inc({"path": "/"})
        return "FastAPI Hello"


    @app.get("/metrics")
    async def handle_metrics(request: Request, accept: List[str] = Header(None)):
        content, http_headers = render(REGISTRY, accept)
        return Response(content=content, media_type=http_headers["Content-Type"])


    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app)

Examples in the ``examples/frameworks`` directory show how aioprometheus can
be used within various web application frameworks.

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
