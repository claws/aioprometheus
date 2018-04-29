User Guide
==========

This section of the documentation provides information about how to use
`aioprometheus`.


Install
-------

The current release of `aioprometheus` is available from PyPI. Use ``pip``
to install it.

.. code-block:: console

    $ pip install aioprometheus


Instrumenting
-------------

Prometheus provides four kinds of metrics that can be used to instrument
your software:

- Counter,
- Gauge,
- Summary and
- Histogram.

More details on the metrics types can be found
`here <https://prometheus.io/docs/concepts/metric_types/>`_.


Counter
+++++++

A counter is a cumulative metric that represents a single numerical value
that only ever goes up. A counter is typically used to count requests
served, tasks completed, errors occurred, etc. Counters should not be used
to expose current counts of items whose number can also go down, e.g. the
number of currently running coroutines. Use gauges for this use case.

.. code-block:: python

    from aioprometheus import Counter

    uploads_metric = Counter("file_uploads_total", "File total uploads.")
    uploads_metric.inc({'type': "png"})


Gauge
+++++

A Gauge is a metric that represents a single numerical value that can
arbitrarily go up and down.

.. code-block:: python

    from aioprometheus import Gauge

    ram_metric = Gauge("memory_usage_bytes", "Memory usage in bytes.")
    ram_metric.set({'type': "virtual"}, 100)
    ram_metric.inc({'type': "virtual"})
    ram_metric.dec({'type': "virtual"})
    ram_metric.add({'type': "virtual"}, 5)
    ram_metric.sub({'type': "virtual"}, -5)


Summary
+++++++

A Summary captures individual observations from an event or sample stream
and summarizes them in a manner similar to traditional summary statistics.

A summary metrics provides:

    #. sum of observations,
    #. observation count,
    #. rank estimations.

.. code-block:: python

    from aioprometheus import Summary

    http_access =  Summary("http_access_time", "HTTP access time")
    http_access.add({'time': '/static'}, 3.142)


Histogram
+++++++++

A Histogram tracks the size and number of events in buckets.

You can use Histograms for aggregatable calculation of quantiles. The set
of buckets used can be overridden by passing `buckets` keyword argument to
``Histogram``.

.. code-block:: python

    from aioprometheus import Histogram

    http_access =  Histogram("http_access_time", "HTTP access time")
    http_access.add({'time': '/static'}, 3.142)


Labels
------

All metrics have labels which allow the grouping of related time series.

See `best practices <https://prometheus.io/docs/practices/naming/>`_
and `labels <https://prometheus.io/docs/practices/instrumentation/#use-labels>`_
for more information of this topic.

To add a metric to a collector you first identify it with a label. In the
following example a Gauge collector is created for tracking memory usage.
Then a specific metric is created within the collector to track virtual
memory usage:

.. code-block:: python

    ram_metric = Gauge("memory_usage_bytes", "Memory usage in bytes.")
    ram_metric.set({'type': "virtual"}, 100)

A single collector is capable of store multiple metric instances. For
example, the swap memory could also be monitored using this collector:

.. code-block:: python

    ram_metric.set({'type': "swap"}, 100.1)


Const labels
++++++++++++

When you create a collector you can also add constant labels. These constant
labels will be included with all the metrics gathered by that collector. This
avoids needing to constantly add extra labels when updating the metric.

So this example without const labels

.. code-block:: python

    host = socket.gethostname()
    ram_metric = Gauge("memory_usage_bytes", "Memory usage in bytes.")
    ram_metric.set({'type': "virtual", 'host': host}, 100)
    ram_metric.set({'type': "swap", 'host': host}, 100)

is the same as this one with const labels:

.. code-block:: python

    host = socket.gethostname()
    ram_metric = Gauge(
        "memory_usage_bytes", "Memory usage in bytes.",
        const_labels={'host': host})
    ram_metric.set({'type': "virtual"}, 100)
    ram_metric.set({'type': "swap"}, 100)


Exporting Metrics
-----------------

Metrics are exposed to the Prometheus server via a HTTP endpoint. The metrics
can retrieved in two different formats; text and binary.


Simple Example
++++++++++++++

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

The metrics service also responds to requests sent to its ``/`` route. The
response is simple HTML. This route can be useful as a Kubernetes ``/healthz``
style health indicator as it does not incur any overhead within the service
to serialize a full metrics response.

.. code-block:: console

    $ curl http://127.0.0.1:50624/
    <html><body><a href='/metrics'>metrics</a></body></html>


Application Example
+++++++++++++++++++

A more representative example is shown below. It implements an application
class that uses the ``aioprometheus`` package to collect application metrics
and expose them on a service endpoint.

.. literalinclude:: ../../examples/app-example.py
    :language: python3

The example can be run using

.. code-block:: console

    (env) $ python app-example.py
    Serving prometheus metrics on: http://127.0.0.1:50624/metrics

You can use the ``curl`` command line tool to fetch metrics manually or use
the helper script described in the next section.


Checking examples using helper script
-------------------------------------

There is a script in the examples directory that emulates Prometheus server
scraping a metrics service endpoint. You can specify a particular format to
use (e.g. text or binary). If no format is specified then it will randomly
choose a format each time it requests metrics.

.. code-block:: console

    usage: metrics-fetcher.py [-h] [--url URL] [--format FORMAT]
                            [--interval INTERVAL] [--debug]

    Metrics Fetcher

    optional arguments:
    -h, --help           show this help message and exit
    --url URL            The metrics URL
    --format FORMAT      Metrics response format (i.e. 'text' or 'binary'
    --interval INTERVAL  The number of seconds between metrics requests
    --debug              Show debug output


Example:

.. code-block:: console

    $ python metrics-fetcher.py --url=http://127.0.0.1:50624/metrics --format=text --interval=2.0


Checking Example using Prometheus
---------------------------------

Once an example is running you can configure Prometheus to begin scraping
it's metrics by creating or updating the configuration file passed to
Prometheus. Using the official Prometheus
`documentation <https://prometheus.io/docs/operating/configuration/>`_
we can create a minimal configuration file to scrape the example application.

.. code-block:: yaml

    global:
      scrape_interval:     15s # By default, scrape targets every 15 seconds.
      evaluation_interval: 15s # By default, scrape targets every 15 seconds.

    scrape_configs:
      - job_name:       'test-app'

        # Override the global default and scrape targets from this job every
        # 5 seconds.
        scrape_interval: 5s
        scrape_timeout: 10s

        target_groups:
          - targets: ['localhost:50624']
            labels:
              group: 'dev'

We can then run Prometheus and configure it using the configuration file.

.. code-block:: console

    $ ./prometheus -config.file my-prom-config.yaml

Once Prometheus is running you can access at `localhost:9090 <http://localhost:9090/>`_
and can observe the metrics from the example.


Decorators
----------

A number of different decorators are provided to help simplify the process of
instrumenting your code. As the ``aioprometheus`` library is targeting use in
long running ``asyncio`` based applications, the decorators return a
coroutine object. However, the wrapped function does not have to be a
coroutine.

The example below demonstrates how the ``@timer`` decorator can be used to
time how long it takes to run a function.

.. literalinclude:: ../../examples/decorator_timer.py
    :language: python3

The following example demonstrates how the ``@inprogress`` decorator can be
used to track how many requests are in progress.

.. literalinclude:: ../../examples/decorator_inprogress.py
    :language: python3

The next example demonstrates how the ``@count_exceptions`` decorator can be
used to track the number of exceptions that occur in a function block.

.. literalinclude:: ../../examples/decorator_count_exceptions.py
    :language: python3


Push Gateway
------------

Another method of exposing metrics is to push them to a gateway that will
get scraped by Prometheus.

Prometheus provides a push gateway intermediary that can be used to help
monitor components that can not be scraped directly. They might be behind a
firewall or might be too short lived. The push gateway allows you to push
time series data to it which ensures that data is always exposed reliably
via the pull model.

.. code-block:: python

    from aioprometheus import Counter, Pusher, Registry

    p = Pusher("my-job", "http://127.0.0.1:61423", loop=self.loop)
    registry = Registry()
    c = Counter("total_requests", "Total requests.", {})
    registry.register(c)

    c.inc({'url': "/p/user"})

    # Push to the pushgateway
    resp = await p.replace(registry)
