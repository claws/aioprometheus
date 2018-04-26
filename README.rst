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


Example
-------

.. code-block:: console

    #!/usr/bin/env python
    '''
    This example demonstrates how a single Counter metric collector can be created
    and exposed via a HTTP endpoint.
    '''
    import asyncio
    import socket
    from aioprometheus import Counter, Service


    if __name__ == '__main__':

        def on_timer_expiry(loop, events_collector):
            ''' Update the metric periodically '''
            events_collector.inc({'kind': 'timer_expiry'})
            loop.call_later(1.0, on_timer_expiry, loop, events_collector)

        loop = asyncio.get_event_loop()

        svr = Service(loop=loop)

        events_collector = Counter(
            "events",
            "Number of events.",
            const_labels={'host': socket.gethostname()})

        svr.registry.register(events_collector)

        loop.run_until_complete(svr.start())
        print('Serving prometheus metrics on: {}'.format(svr.metrics_url))

        loop.call_later(1.0, on_timer_expiry, loop, events_collector)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(svr.stop())
        loop.close()

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
    Serving prometheus metrics on: http://0.0.0.0:50624/metrics

In another terminal fetch the metrics using the ``curl`` command line tool
to verify they can be retrieved by Prometheus server.

By default metrics will be returned in plan text format.

.. code-block:: console

    $ curl http://0.0.0.0:50624/metrics
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 33
    $ curl http://0.0.0.0:50624/metrics -H 'Accept: text/plain; version=0.0.4'
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 36

Similarly, you can request metrics in binary format, though this will be hard
to read on the command line.

.. code-block:: console

    $ curl http://0.0.0.0:50624/metrics -H "ACCEPT: application/vnd.google.protobuf; proto=io.prometheus.client.MetricFamily; encoding=delimited"

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
