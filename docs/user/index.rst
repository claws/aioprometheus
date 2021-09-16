.. _user-guide-label:

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
aioprometheus. In the example below its a Counter metric. Next, instantiate
the metric with a name and a help string. Finally, update the metric, which
in this case is an increment.

.. code-block:: python

    from aioprometheus import Counter

    events_counter = Counter(
        "events_counter",
        "Total number of events.",
    )

    events_counter.inc({"kind": "event A"})

A number of convenience decorator functions are included in aioprometheus that
can assist with automatically updating metrics. The ``examples`` directory
contains various decorators examples.

Once your software is instrumented with metrics you'll want to expose them to
Prometheus or a compatible metrics collector. There are multiple strategies
available for this and the right choice depends on the kind of thing being
instrumented. See the exporting metrics section below.

The following sections describe instrumenting, exposing metrics, decorators
and the push gateway in more detail.


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

By default, each metric gets registered into the default collector registry
which is available at ``aioprometheus.REGISTRY``. Metrics accept a ``registry``
keyword argument if you need to supply your own registry. The registry is
important later when you want to expose your metrics to a collector.


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
    http_access.observe({'time': '/static'}, 3.142)

The default invariants ([(0.50, 0.05), (0.90, 0.01), (0.99, 0.001)])
can be overridden by passing `invariants` keyword argument to Summary.

.. code-block:: python

    from aioprometheus import Summary

    http_access =  Summary(
        "http_access_time",
        "HTTP access time",
        invariants=[(0.50, 0.05), (0.99, 0.001)])


Histogram
+++++++++

A Histogram tracks the size and number of events in buckets.

You can use Histograms for aggregatable calculation of quantiles.


.. code-block:: python

    from aioprometheus import Histogram

    http_access =  Histogram("http_access_time", "HTTP access time")
    http_access.observe({'time': '/static'}, 3.142)

The default buckets cover the range 0.005, 0.01, 0.025, 0.05, 0.1,
0.25, 0.5, 1.0, 2.5, 5.0, 10.0. All bucket ranges will include a
+Inf bucket. The buckets can be overridden by passing `buckets` keyword
argument to Histogram.

.. code-block:: python

    from aioprometheus import Histogram

    http_access =  Histogram(
        "http_access_time",
        "HTTP access time",
        buckets=[0.1, 0.5, 1.0, 5.0])


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

    ram_metric = Gauge(
        "memory_usage_bytes", "Memory usage in bytes.",
        const_labels={'host': socket.gethostname()})
    ram_metric.set({'type': "virtual"}, 100)
    ram_metric.set({'type': "swap"}, 100)


Exporting Metrics
-----------------

Once you have instrumented your code with various metrics you'll want to
expose them to Prometheus or a compatible metrics collector. Metrics are
exposed to the Prometheus server via a HTTP endpoint. There are multiple
strategies available for this and the right choice depends on the kind of
application being instrumented.


Web Frameworks
++++++++++++++

The aioprometheus package can be used within web application frameworks
such as ``Starlette``, ``FastAPI``, ``aiohttp`` and ``Quart``.

An example showing how aioprometheus can be used with FastAPI is shown
below.

.. literalinclude:: ../../examples/frameworks/fastapi_example.py
    :language: python3

There are more examples in the ``examples/frameworks`` directory showing
how aioprometheus can be used with other web application frameworks.


Other Applications
++++++++++++++++++

Other applications such as long running distributed system processes like a
socket relay or some kind of message adapter can embed the aioprometheus
metrics Service to facilitate exporting metrics.

The example below shows a long running application that monitors various
process metrics and exposes them using the Service endpoint.

.. literalinclude:: ../../examples/app-example.py
    :language: python3

This example requires some optional extras to be installed.

.. code-block:: console

    $ pip install aioprometheus[aiohttp]

The example can be run using

.. code-block:: console

    (env) $ python app-example.py
    Serving prometheus metrics on: http://127.0.0.1:8000/metrics

You can open the URL in a browser or use the ``curl`` command line tool to
fetch metrics manually.

The metrics service also responds to requests sent to its ``/`` route. The
response is simple HTML. This route can be useful as a Kubernetes ``/healthz``
style health indicator as it does not incur any overhead within the service
to serialize a full metrics response.

.. code-block:: console

    $ curl http://127.0.0.1:8000/
    <html><body><a href='/metrics'>metrics</a></body></html>

The next example shows how to use the Service without any of the extra
application complexity in the example above.

.. literalinclude:: ../../examples/simple-example.py
    :language: python3

In the example above the counter metric is tracking the number of while
loop iterations executed by the updater coroutine.

The Service is responsible for responding to metrics requests. The Service
accepts various arguments such as the interface and port to bind to. The
Service uses a collector registry when responding to requests for metrics.
The service will use the default collector registry if one is not passed in.

The Service is started and then a coroutine is started to periodically
update the metric to simulate progress.

This example requires some optional extras to be installed.

.. code-block:: console

    $ pip install aioprometheus[aiohttp]

The script can be run using:

.. code-block:: console

    (venv) $ python simple-example.py
    Serving prometheus metrics on: http://127.0.0.1:8000/metrics

You can open the URL in a browser or use the ``curl`` command line tool to
fetch metrics manually.

By default metrics will be returned in plan text format.

.. code-block:: console

    $ curl http://127.0.0.1:8000/metrics
    # HELP events Number of events.
    # TYPE events counter
    events{host="alpha",kind="timer_expiry"} 33


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
          - targets: ['localhost:8000']
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
instrumenting your code. The decorators return a regular function if the
wrapped function is a regular function or an awaitable if the wrapped function
is a coroutine function.

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

Another method of exposing metrics is to push them to an intermediary that will
get scraped by Prometheus. The Prometheus PushGateway exists for this purpose.

This strategy can be useful to obtain metrics from components that can not be
scraped directly. They might be behind a firewall or might be too short lived.

The Prometheus Push Gateway allows you to push time series data to it which
ensures that data is always exposed reliably via the pull model.

The aioprometheus package provides a Pusher object that can be used within
your application to push metrics to a Prometheus Push Gateway. The Pusher
allows you to specify a job name as well as additional grouping keys.

The grouping keys get added to the Push Gateway URL using the rules described
`here <https://github.com/prometheus/pushgateway/blob/master/README.md#url>`__.
See `here <https://github.com/prometheus/pushgateway/blob/master/README.md#about-the-job-and-instance-labels>`__
for how to configure Prometheus to best scrape metrics from the Push Gateway.

The Pusher requires the `aiohttp` optional extra to be installed.

.. code-block:: console

    $ pip install aioprometheus[aiohttp]

.. code-block:: python

    from aioprometheus import Counter, Pusher, Registry

    PUSH_GATEWAY_ADDR = "http://127.0.0.1:61423"
    p = Pusher("my-job", PUSH_GATEWAY_ADDR, grouping_key={"instance": "127.0.0.1:1234"})
    registry = Registry()
    c = Counter("total_requests", "Total requests.", {})
    registry.register(c)

    c.inc({'url': "/p/user"})

    # Push to the pushgateway
    resp = await p.replace(registry)
