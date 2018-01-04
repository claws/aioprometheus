.. image:: https://travis-ci.org/claws/aioprometheus.svg?branch=master
    :target: https://travis-ci.org/claws/aioprometheus

.. image:: https://img.shields.io/pypi/v/aioprometheus.svg
    :target: https://pypi.python.org/pypi/aioprometheus

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

.. literalinclude:: ../examples/simple-example.py
    :language: python3

The example above shows a single Counter metric collector being created
and exposed via a HTTP endpoint.

The counter metric is created to track the number of iterations. This
example uses a timer callback to periodically increment the metric
tracking iterations. In a realistic application a metric might track the
number of requests, etc.

Following typical ``asyncio`` usage, an event loop is instantiated first
then a metrics service is instantiated. The metrics service is responsible
for managing the various metrics collectors and responding to Prometheus
server when it requests metrics.

The server accepts various arguments such as the interface and port to bind
to. The service will create a new collector registry if one is not passed
in. A collector registry holds the various metrics collectors that will be
exposed by the service.

The example script can be run using:

.. code-block:: console

    (env) $ cd examples
    (env) $ python simple-example.py
    Serving prometheus metrics on: http://127.0.0.1:50624/metrics

In another terminal fetch the metrics using the ``curl`` command line tool
to verify they can be retrieved by Prometheus server.

By default metrics will be returned in plan text format.

.. code-block:: console

    $ curl http://127.0.0.1:50624/metrics
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 33
    $ curl http://127.0.0.1:50624/metrics -H 'Accept: text/plain; version=0.0.4'
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 36

Similarly, you can request metrics in binary format, though this will be hard
to read on the command line.

.. code-block:: console

    $ curl http://127.0.0.1:50624/metrics -H "ACCEPT: application/vnd.google.protobuf; proto=io.prometheus.client.MetricFamily; encoding=delimited"

There are more examples in the ``examples`` directory. The ``app-example.py``
file will likely be of interest as it provides a more representative
application example.

A number of convenience decorator functions are also available to assist with
updating metrics.


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

