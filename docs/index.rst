.. image:: https://github.com/claws/aioprometheus/workflows/Python%20Package%20Workflow/badge.svg?branch=master
    :target: https://github.com/claws/aioprometheus/actions?query=branch%3Amaster

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black

aioprometheus
=============

`aioprometheus` is a Prometheus Python client library for asyncio-based
applications.

It provides asyncio based applications with a metrics collection and serving
capability for use with the `Prometheus <https://prometheus.io/>`_ monitoring
and alerting system.

It supports text and binary data formats as well as the ability to push
metrics to a gateway.

The project source code can be found `here <https://github.com/claws/aioprometheus>`_.


.. toctree::
   :maxdepth: 1
   :hidden:

   user/index
   dev/index
   api/index


Example
-------

The example below shows a single Counter metric collector being created
and exposed via a HTTP endpoint.

.. literalinclude:: ../examples/simple-example.py
    :language: python3

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

    $ curl http://127.0.0.1:5000/metrics -H 'Accept: text/plain; version=0.0.4'
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 36

Similarly, you can request metrics in binary format, though this will be hard
to read on the command line.

.. code-block:: console

    $ pip install aioprometheus[binary]  # required

    $ curl http://127.0.0.1:5000/metrics -H "ACCEPT: application/vnd.google.protobuf; proto=io.prometheus.client.MetricFamily; encoding=delimited"

The metrics service also responds to requests sent to its ``/`` route. The
response is simple HTML. This route can be useful as a Kubernetes health
indicator as it does not incur any overhead within the service to
serialize a full metrics response.

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
be used within an existing FastAPI, aiohttp or quart application instead of
creating a separate aioprometheus.Service endpoint to handle metrics. The
FastAPI example is shown below.

.. literalinclude:: ../examples/frameworks/fastapi_example.py
    :language: python3


License
-------

`aioprometheus` is released under the MIT license.

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package which
was released under the MIT license. `aioprometheus` continues to use the MIT
license and contains a copy of the orignal MIT license from the
`prometheus-python` project as instructed by the original license.


Origins
-------

`aioprometheus` originates from the (now deprecated)
`prometheus python <https://github.com/slok/prometheus-python>`_ package.
Many thanks to `slok <https://github.com/slok>`_ for developing
prometheus-python. I have taken the original work and modified it to meet
the needs of my asyncio-based applications, added the histogram metric,
integrated support for binary format, updated and extended tests, added docs,
decorators, etc.

