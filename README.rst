.. image:: https://travis-ci.org/claws/aioprometheus.svg?branch=master
    :target: https://travis-ci.org/claws/aioprometheus

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus


aioprometheus
=============

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications. It provides metrics collection and serving capabilities,
supports multiple data formats and pushing metrics to a gateway.

The project documentation can be found on
`ReadTheDocs <http://aioprometheus.readthedocs.org/>`_.


Install
-------

.. code-block:: console

    $ pip install aioprometheus

A Prometheus Push Gateway client and ASGI service are also provided, but the
dependencies are not installed by default. You can install them alongside
`aioprometheus` by running:

.. code-block:: console

    $ pip install aioprometheus[aiohttp]


Example
-------

The example below shows a single Counter metric collector being created
and exposed via a HTTP endpoint.

.. code-block:: python

    #!/usr/bin/env python
    """
    This example demonstrates how a single Counter metric collector can be created
    and exposed via a HTTP endpoint.
    """
    import asyncio
    import socket
    from aioprometheus import Counter, Service


    if __name__ == "__main__":

        async def main(svr: Service) -> None:

            events_counter = Counter(
                "events", "Number of events.", const_labels={"host": socket.gethostname()}
            )
            svr.register(events_counter)
            await svr.start(addr="127.0.0.1", port=5000)
            print(f"Serving prometheus metrics on: {svr.metrics_url}")

            # Now start another coroutine to periodically update a metric to
            # simulate the application making some progress.
            async def updater(c: Counter):
                while True:
                    c.inc({"kind": "timer_expiry"})
                    await asyncio.sleep(1.0)

            await updater(events_counter)

        loop = asyncio.get_event_loop()
        svr = Service()
        try:
            loop.run_until_complete(main(svr))
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(svr.stop())
        loop.close()

In this simple example the counter metric is tracking the number of
while loop iterations executed by the updater coroutine. In a realistic
application a metric might track the number of requests, etc.

Following typical ``asyncio`` usage, an event loop is instantiated first
then a metrics service is instantiated. The metrics service is responsible
for managing metric collectors and responding to metrics requests.

The service accepts various arguments such as the interface and port to bind
to. A collector registry is used within the service to hold metrics
collectors that will be exposed by the service. The service will create a new
collector registry if one is not passed in.

A counter metric is created and registered with the service. The service is
started and then a coroutine is started to periodically update the metric
to simulate progress.

The example script can be run using:

.. code-block:: console

    (venv) $ cd examples
    (venv) $ python simple-example.py
    Serving prometheus metrics on: http://127.0.0.1:5000/metrics

In another terminal fetch the metrics using the ``curl`` command line tool
to verify they can be retrieved by Prometheus server.

By default metrics will be returned in plan text format.

.. code-block:: console

    $ curl http://127.0.0.1:5000/metrics
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 33

Similarly, you can request metrics in binary format, though this will be hard
to read on the command line.

.. code-block:: console

    $ curl http://127.0.0.1:5000/metrics -H "ACCEPT: application/vnd.google.protobuf; proto=io.prometheus.client.MetricFamily; encoding=delimited"

The metrics service also responds to requests sent to its ``/`` route. The
response is simple HTML. This route can be useful as a Kubernetes ``/healthz``
style health indicator as it does not incur any overhead within the service
to serialize a full metrics response.

.. code-block:: console

    $ curl http://127.0.0.1:5000/
    <html><body><a href='/metrics'>metrics</a></body></html>

The aioprometheus package provides a number of convenience decorator
functions that can assist with updating metrics.

There ``examples`` directory contains many examples showing how to use the
aioprometheus package. The ``app-example.py`` file will likely be of interest
as it provides a more representative application example that the simple
example shown above.

Examples in the ``examples/frameworks`` directory show how aioprometheus can
be used within existing aiohttp, quart and vibora applications instead of
creating a separate aioprometheus.Service endpoint to handle metrics. The
vibora example is shown below.

.. code-block:: python

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


License
-------

`aioprometheus` is released under the MIT license.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package which
was released under the MIT license. `aioprometheus` continues to use the MIT
license and contains a copy of the orignal MIT license from the
`prometheus-python` project as instructed by the original license.
