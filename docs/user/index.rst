User Guide
==========

This section of the documentation provides information about how to use
`aioprometheus`.


Install
-------

The current realease of `aioprometheus` is available from PyPI. Use ``pip``
to install it.

.. code-block:: console

    $ pip install aioprometheus


Install optional binary formatter
+++++++++++++++++++++++++++++++++

If you want to make use of the binary formatter then a separate package that
provides the Google Protocol Buffer codec must be installed separately.

.. code-block:: console

    $ pip install prometheus-metrics-proto

This command will build and install the ``prometheus_metrics_proto`` extension
module that aioprometheus can then use to provide metrics in the binary format.


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

A single collector is capable of store multiple metric. For example, the
swap memory could also be monitored using this collector:

.. code-block:: python

    ram_metric.set({'type': "swap"}, 100.1)


Const labels
++++++++++++

When you create a collector you can also add constant labels. These constant
labels will be included with all the metrics gathered by that collector. For
example this example without const labels

.. code-block:: python

    host = socket.gethostname()
    ram_metric = Gauge("memory_usage_bytes", "Memory usage in bytes.")
    ram_metric.set({'type': "virtual", 'host': host}, 100)
    ram_metric.set({'type': "swap", 'host': host}, 100)

is the same as this one with const labels:

.. code-block:: python

    host = socket.gethostname()
    ram_metric = Gauge(
        "memory_usage_bytes", "Memory usage in bytes.",  {'host': host})
    ram_metric.set({'type': "virtual"}, 100)
    ram_metric.set({'type': "swap"}, 100)


Decorators
++++++++++

A number of different decorators are provided to help simplfy the process of
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


Exporting Metrics
-----------------

HTTP
++++

Metrics are typically exposed to the Prometheus server via a HTTP endpoint.
The metrics can also be exposed using two different formats; text and binary.

The following example shows how a metrics service can be instantiated along
with a Counter. Following typical ``asyncio`` usage, an event loop is
instantiated first then a Prometheus metrics service is instantiated.
The server accepts various arguments such as the interface and port to bind
to.

.. literalinclude:: ../../examples/docs-example.py
    :language: python3

The service can also be passed a specific registry to use or if none is
explicitly defined it will create a registry. A registry holds the
various metrics collectors that will be exposed by the service.

Next, a counter metric is created to track the number of iterations. This
example uses a timer callback to periodically increment the metric
tracking iterations. In a realistic application a metric might track the
number of requests, etc.

The example can be run using:

.. code-block:: console

    $ python docs-example.py
    serving prometheus metrics on: http://0.0.0.0:60405/metrics

You can visit `http://0.0.0.0:60405/metrics <http://0.0.0.0:60405/metrics>`_
to view the metrics.


Checking Metrics Server using curl
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check the different formats with curl:

Default (Text 0.0.4):

.. code-block:: console

    $ curl 'http://127.0.0.1:60405/metrics'

Text (0.0.4):

.. code-block:: console

    $ curl 'http://127.0.0.1:60405/metrics' -H 'Accept: text/plain; version=0.0.4'

Protobuf (0.0.4) [only if aioprometheus-binary-format is installed]:

.. code-block:: console

    $ curl 'http://127.0.0.1:60405/metrics' -H 'Accept: application/vnd.google.protobuf; proto=io.prometheus.client.MetricFamily; encoding=delimited'


Checking Metrics Server using Prometheus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the example is running you can configure Prometheus to begin scraping
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
          - targets: ['localhost:60405']
            labels:
              group: 'dev'

We can then run Prometheus and configure it using the configuration file.

.. code-block:: console

    $ ./prometheus -config.file my-prom-config.yaml

Once Prometheus is running you can access at `localhost:9090 <http://localhost:9090/>`_
and can observe the metrics from the example.


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
