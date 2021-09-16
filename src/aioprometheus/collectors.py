import enum
import json
import re
from collections import OrderedDict
from typing import Dict, List, Sequence, Tuple, Union, cast

import quantile

from aioprometheus.mypy_types import LabelsType, NumericValueType

from . import histogram
from .metricdict import MetricDict

# Used to return the ordered pairs (which is not necessary but is useful
# for consistency).
decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)


METRIC_NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
RESTRICTED_LABELS_NAMES = ("job",)
RESTRICTED_LABELS_PREFIXES = ("__",)

POS_INF = float("inf")
NEG_INF = float("-inf")


class MetricsTypes(enum.Enum):
    counter = 0
    gauge = 1
    summary = 2
    untyped = 3
    histogram = 4


class Collector:
    """Base class for all collectors.

    **Metric names and labels**

    Every time series is uniquely identified by its metric name and a set
    of key-value pairs, also known as labels.

    Labels enable Prometheus's dimensional data model: any given combination
    of labels for the same metric name identifies a particular dimensional
    instantiation of that metric (for example: all HTTP requests that used
    the method POST to the /api/tracks handler). The query language allows
    filtering and aggregation based on these dimensions. Changing any label
    value, including adding or removing a label, will create a new time
    series.

    Label names may contain ASCII letters, numbers, as well as underscores.
    They must match the regex ``[a-zA-Z_][a-zA-Z0-9_]*``. Label names
    beginning with ``__`` are reserved for internal use.

    **Samples**

    Samples form the actual time series data. Each sample consists of:

      - a float64 value
      - a millisecond-precision timestamp

    **Notation**

    Given a metric name and a set of labels, time series are frequently
    identified using this notation:

    .. code-block:: console

        <metric name>{<label name>=<label value>, ...}

    For example, a time series with the metric name
    ``api_http_requests_total`` and the labels ``method="POST"`` and
    ``handler="/messages"`` could be written like this:

    .. code-block:: console

        api_http_requests_total{method="POST", handler="/messages"}

    """

    kind = MetricsTypes.untyped

    def __init__(
        self,
        name: str,
        doc: str,
        const_labels: LabelsType = None,
        registry: "Registry" = None,
    ) -> None:
        """
        :param name: The name of the metric.

        :param doc: A short description of the metric.

        :param const_labels: Labels that should always be included with all
          instances of this metric.

        :param registry: A collector registry that is responsible for
          rendering the metric into various formats. When a registry is
          not supplied then the metric will be registered with the default
          registry.
        """
        if not METRIC_NAME_RE.match(name):
            raise ValueError(f"Invalid metric name: {name}")
        self.name = name
        self.doc = doc

        if const_labels:
            self._check_labels(const_labels)
            self.const_labels = const_labels
        else:
            self.const_labels = {}

        self.values = MetricDict()

        # Register metric with a Registry or the default registry
        if registry is None:
            registry = get_registry()
        registry.register(self)

    def set_value(self, labels: LabelsType, value: NumericValueType) -> None:
        """Sets a value in the container"""
        if labels:
            self._check_labels(labels)
        self.values[labels] = value

    def get_value(self, labels: LabelsType) -> NumericValueType:
        """Gets a value in the container.

        :raises: KeyError if an item with matching labels is not present.
        """
        return self.values[labels]

    def get(self, labels: LabelsType) -> NumericValueType:
        """Gets a value in the container.

        Handy alias for `get_value`.

        :raises: KeyError if an item with matching labels is not present.
        """
        return self.get_value(labels)

    def _check_labels(self, labels: LabelsType) -> bool:
        """Check validity of label names.

        :raises: ValueError if labels are invalid
        """
        for k, _v in labels.items():
            # Check reserved labels
            if k in RESTRICTED_LABELS_NAMES:
                raise ValueError(f"Invalid label name: {k}")

            if self.kind == MetricsTypes.histogram:
                if k in ("le",):
                    raise ValueError(f"Invalid label name: {k}")

            # Check prefixes
            if any(k.startswith(i) for i in RESTRICTED_LABELS_PREFIXES):
                raise ValueError(f"Invalid label prefix: {k}")

        return True

    def get_all(self) -> List[Tuple[LabelsType, NumericValueType]]:
        """
        Returns a list populated with 2-tuples. The first element is
        a dict of labels and the second element is the value of the metric
        itself.
        """
        items = self.values.items()

        result = []
        for k, _v in items:
            key = {}  # type: LabelsType
            # Check if is a single value dict (custom empty key)
            if not k or k == MetricDict.EMPTY_KEY:
                pass
            else:
                key = decoder.decode(k)
            result.append((key, self.get(k)))

        return result

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.name == other.name
            and self.doc == other.doc  # type: ignore
            and self.values == other.values  # type: ignore
        )


class Counter(Collector):
    """
    A counter is a cumulative metric that represents a single numerical value
    that only ever goes up. A counter is typically used to count requests
    served, tasks completed, errors occurred, etc. Counters should not be used
    to expose current counts of items whose number can also go down, e.g. the
    number of currently running coroutines. Use gauges for this use case.

    Examples:
    - Number of requests processed
    - Number of items that were inserted into a queue
    - Total amount of data that a system has processed
    """

    kind = MetricsTypes.counter

    def get(self, labels: LabelsType) -> NumericValueType:
        """Get the Counter value matching an arbitrary group of labels.

        :raises: KeyError if an item with matching labels is not present.
        """
        return self.get_value(labels)

    def set(self, labels: LabelsType, value: NumericValueType) -> None:
        """Set the counter to an arbitrary value."""
        self.set_value(labels, value)

    def inc(self, labels: LabelsType) -> None:
        """Increments the counter by 1."""
        self.add(labels, 1)

    def add(self, labels: LabelsType, value: NumericValueType) -> None:
        """Add the given value to the counter.

        :raises: ValueError if the value is negative. Counters can only
          increase.
        """
        value = cast(Union[float, int], value)  # typing check, no runtime behaviour.
        if value < 0:
            raise ValueError("Counters can't decrease")

        try:
            current = self.get_value(labels)
        except KeyError:
            current = 0

        current = cast(
            Union[float, int], current
        )  # typing check, no runtime behaviour.
        self.set_value(labels, current + value)


class Gauge(Collector):
    """
    A gauge is a metric that represents a single numerical value that can
    arbitrarily go up and down.

    Examples of Gauges include:
    - Inprogress requests
    - Number of items in a queue
    - Free memory
    - Total memory
    - Temperature

    Gauges can go both up and down.
    """

    kind = MetricsTypes.gauge

    def set(self, labels: LabelsType, value: NumericValueType) -> None:
        """Set the gauge to an arbitrary value."""
        self.set_value(labels, value)

    def get(self, labels: LabelsType) -> NumericValueType:
        """Get the gauge value matching an arbitrary group of labels.

        :raises: KeyError if an item with matching labels is not present.
        """
        return self.get_value(labels)

    def inc(self, labels: LabelsType) -> None:
        """Increments the gauge by 1."""
        self.add(labels, 1)

    def dec(self, labels: LabelsType) -> None:
        """Decrement the gauge by 1."""
        self.add(labels, -1)

    def add(self, labels: LabelsType, value: NumericValueType) -> None:
        """Add the given value to the Gauge.

        The value can be negative, resulting in a decrease of the gauge.
        """
        value = cast(Union[float, int], value)  # typing check, no runtime behaviour.

        try:
            current = self.get_value(labels)
        except KeyError:
            current = 0
        current = cast(
            Union[float, int], current
        )  # typing check, no runtime behaviour.

        self.set_value(labels, current + value)

    def sub(self, labels: LabelsType, value: NumericValueType) -> None:
        """Subtract the given value from the Gauge.

        The value can be negative, resulting in an increase of the gauge.
        """
        value = cast(Union[float, int], value)  # typing check, no runtime behaviour.
        self.add(labels, -value)


class Summary(Collector):
    """
    A Summary metric captures individual observations from an event or sample
    stream and summarizes them in a manner similar to traditional summary
    statistics:

    1. sum of observations,
    2. observation count,
    3. rank estimations.

    Example use cases for Summaries:
    - Response latency
    - Request size
    """

    kind = MetricsTypes.summary

    REPR_STR = "summary"
    DEFAULT_INVARIANTS = ((0.50, 0.05), (0.90, 0.01), (0.99, 0.001))
    SUM_KEY = "sum"
    COUNT_KEY = "count"

    def __init__(
        self,
        name: str,
        doc: str,
        const_labels: LabelsType = None,
        registry: "Registry" = None,
        invariants: Sequence[Tuple[float, float]] = DEFAULT_INVARIANTS,
    ) -> None:
        super().__init__(name, doc, const_labels=const_labels, registry=registry)
        self.invariants = invariants

    def add(self, labels: LabelsType, value: NumericValueType) -> None:
        """Add a single observation to the summary"""

        value = cast(Union[float, int], value)  # typing check, no runtime behaviour.
        if type(value) not in (float, int):
            raise TypeError("Summary only works with digits (int, float)")

        try:
            e = self.get_value(labels)
        except KeyError:
            # Initialize quantile estimator
            e = quantile.Estimator(*self.invariants)
            self.set_value(labels, e)

        e.observe(float(value))  # type: ignore

    # https://prometheus.io/docs/instrumenting/writing_clientlibs/#summary
    # A summary MUST have the ``observe`` methods
    observe = add

    def get(self, labels: LabelsType) -> Dict[Union[float, str], NumericValueType]:
        """
        Get a dict of values, containing the sum, count and quantiles,
        matching an arbitrary group of labels.

        :raises: KeyError if an item with matching labels is not present.
        """
        return_data = OrderedDict()  # type: Dict[Union[float, str], NumericValueType]

        e = self.get_value(labels)  # type: quantile.Estimator

        # Get invariants data
        for i in e._invariants:  # pylint: disable=protected-access
            q = i._quantile  # pylint: disable=protected-access
            return_data[q] = e.query(q)

        # Set sum and count
        return_data[
            self.COUNT_KEY
        ] = e._observations  # pylint: disable=protected-access
        return_data[self.SUM_KEY] = e._sum  # pylint: disable=protected-access

        return return_data


class Histogram(Collector):
    """
    A histogram samples observations (usually things like request durations
    or response sizes) and counts them in configurable buckets. It also
    provides a sum of all observed values.

    A histogram with a base metric name of <basename> exposes multiple time
    series during a scrape:

      - cumulative counters for the observation buckets, exposed as
        <basename>_bucket{le="<upper inclusive bound>"}
      - the total sum of all observed values, exposed as <basename>_sum
      - the count of events that have been observed, exposed as
        <basename>_count (identical to <basename>_bucket{le="+Inf"} above)

    Example use cases:
    - Response latency
    - Request size
    """

    kind = MetricsTypes.histogram

    REPR_STR = "histogram"
    DEFAULT_BUCKETS = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        POS_INF,
    )
    SUM_KEY = "sum"
    COUNT_KEY = "count"

    def __init__(
        self,
        name: str,
        doc: str,
        const_labels: LabelsType = None,
        registry: "Registry" = None,
        buckets: Sequence[float] = DEFAULT_BUCKETS,
    ) -> None:
        super().__init__(name, doc, const_labels=const_labels, registry=registry)
        self.upper_bounds = buckets

    def add(self, labels: LabelsType, value: NumericValueType) -> None:
        """Add a single observation to the histogram"""

        value = cast(Union[float, int], value)  # typing check, no runtime behaviour.
        if type(value) not in (float, int):
            raise TypeError("Histogram only works with digits (int, float)")

        try:
            h = self.get_value(labels)
            h = cast(histogram.Histogram, h)  # typing check, no runtime behaviour.
        except KeyError:
            # Initialize histogram aggregator
            h = histogram.Histogram(*self.upper_bounds)
            self.set_value(labels, h)

        h.observe(float(value))

    # https://prometheus.io/docs/instrumenting/writing_clientlibs/#histogram
    # A histogram MUST have the ``observe`` methods
    observe = add

    def get(self, labels: LabelsType) -> Dict[Union[float, str], NumericValueType]:
        """
        Get a dict of values, containing the sum, count and buckets,
        matching an arbitrary group of labels.

        :raises: KeyError if an item with matching labels is not present.
        """
        return_data = OrderedDict()  # type: Dict[Union[float, str], NumericValueType]

        h = self.get_value(labels)
        h = cast(histogram.Histogram, h)  # typing check, no runtime behaviour.

        for upper_bound, cumulative_count in h.buckets.items():
            return_data[upper_bound] = cumulative_count  # keys are floats

        # Set sum and count
        return_data[self.COUNT_KEY] = h.observations
        return_data[self.SUM_KEY] = h.sum

        return return_data


# The Registry class exists in this module as part of a strategy to avoid
# circular imports (mostly caused by type annotations).


class Registry:
    """This class implements a container to hold metrics collectors.

    Collectors in the registry must comply with the Collector interface
    which means that they inherit from the base Collector object and implement
    a no-argument method called 'get_all' that returns a list of Metric
    instance objects.
    """

    def __init__(self) -> None:
        self.collectors = {}  # type: Dict[str, Collector]

    def register(self, collector: Collector) -> None:
        """Register a collector into the container.

        The registry provides a container that can be used to access all
        metrics when exposing them into a specific format.

        :param collector: A collector to register in the registry.

        :raises: TypeError if collector is not an instance of
          :class:`Collector`.

        :raises: ValueError if collector is already registered.
        """
        if not isinstance(collector, Collector):
            raise TypeError(f"Invalid collector type: {collector}")

        if collector.name in self.collectors:
            raise ValueError(f"A collector for {collector.name} is already registered")

        self.collectors[collector.name] = collector

    def deregister(self, name: str) -> None:
        """Deregister a collector.

        This will stop the collector metrics from being emitted.

        :param name: The name of the collector to deregister.

        :raises: KeyError if collector is not already registered.
        """
        del self.collectors[name]

    def get(self, name: str) -> Collector:
        """Get a collector by name.

        :param name: The name of the collector to fetch.

        :raises: KeyError if collector is not found.
        """
        return self.collectors[name]

    def get_all(self) -> List[Collector]:
        """Return a list of all collectors"""
        return list(self.collectors.values())

    def clear(self):
        """Clear all registered collectors.

        This function is mainly of use in tests to reset the default registry
        which may be used in multiple tests.
        """
        for name in list(self.collectors.keys()):
            self.deregister(name)


REGISTRY = Registry()


def get_registry() -> Registry:
    """Return the default Registry"""
    return REGISTRY
