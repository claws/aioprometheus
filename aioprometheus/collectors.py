
import collections
import enum
import json
import re

import quantile

from . import histogram
from .metricdict import MetricDict

# Used to return the value ordered (not necessary but for consistency useful)
decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)


METRIC_NAME_RE = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$')
RESTRICTED_LABELS_NAMES = ('job',)
RESTRICTED_LABELS_PREFIXES = ('__',)

POS_INF = float("inf")
NEG_INF = float("-inf")


class MetricsTypes(enum.Enum):
    counter = 0
    gauge = 1
    summary = 2
    untyped = 3
    histogram = 4


class Collector(object):
    ''' Base class for all collectors.

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

    '''

    kind = MetricsTypes.untyped

    def __init__(self, name, doc, const_labels=None):
        if not METRIC_NAME_RE.match(name):
            raise ValueError('Invalid metric name: {}'.format(name))
        self.name = name
        self.doc = doc
        self.const_labels = const_labels

        if const_labels:
            self._label_names_correct(const_labels)
            self.const_labels = const_labels

        self.values = MetricDict()

    def set_value(self, labels, value):
        '''  Sets a value in the container '''
        if labels:
            self._label_names_correct(labels)
        self.values[labels] = value

    def get_value(self, labels):
        '''  Gets a value in the container, exception if isn't present '''
        return self.values[labels]

    def get(self, labels):
        ''' Handy alias '''
        return self.get_value(labels)

    def _label_names_correct(self, labels):
        ''' Check validity of label names.

        :raises: ValueError if labels are invalid
        '''
        for k, v in labels.items():
            # Check reserved labels
            if k in RESTRICTED_LABELS_NAMES:
                raise ValueError("Invalid label name: {}".format(k))

            if self.kind == MetricsTypes.histogram:
                if k in ('le', ):
                    raise ValueError("Invalid label name: {}".format(k))

            # Check prefixes
            if any(k.startswith(i) for i in RESTRICTED_LABELS_PREFIXES):
                raise ValueError("Invalid label prefix: {}".format(k))

        return True

    def get_all(self):
        '''
        Returns a list populated with 2-tuples. The first element is
        a dict of labels and the second element is the value of the metric
        itself.
        '''
        items = self.values.items()

        result = []
        for k, v in items:
            # Check if is a single value dict (custom empty key)
            if not k or k == MetricDict.EMPTY_KEY:
                key = None
            else:
                key = decoder.decode(k)
            result.append((key, self.get(k)))

        return result

    def __eq__(self, other):
        return (
            isinstance(other, Collector) and
            self.name == other.name and
            self.doc == other.doc and
            type(self) == type(other) and
            self.values == other.values)


class Counter(Collector):
    '''
    A counter is a cumulative metric that represents a single numerical value
    that only ever goes up. A counter is typically used to count requests
    served, tasks completed, errors occurred, etc. Counters should not be used
    to expose current counts of items whose number can also go down, e.g. the
    number of currently running coroutines. Use gauges for this use case.

    Examples:
    - Number of requests processed
    - Number of items that were inserted into a queue
    - Total amount of data that a system has processed
    '''

    kind = MetricsTypes.counter

    def get(self, labels):
        ''' Get gets the counter of an arbitrary group of labels '''
        return self.get_value(labels)

    def set(self, labels, value):
        ''' Set is used to set the Counter to an arbitrary value. '''
        self.set_value(labels, value)

    def inc(self, labels):
        ''' Inc increments the counter by 1.'''
        self.add(labels, 1)

    def add(self, labels, value):
        ''' Add will add the given value to the counter.

        :raises: ValueError if the value is negative. Counters can only
          increase.
        '''
        if value < 0:
            raise ValueError("Counters can't decrease")

        try:
            current = self.get_value(labels)
        except KeyError:
            current = 0

        self.set_value(labels, current + value)


class Gauge(Collector):
    '''
    A Gauge is a metric that represents a single numerical value that can
    arbitrarily go up and down.

    Examples of Gauges include:
    - Inprogress requests
    - Number of items in a queue
    - Free memory
    - Total memory
    - Temperature

     Gauges can go both up and down.
    '''

    kind = MetricsTypes.gauge

    def set(self, labels, value):
        ''' Set sets the Gauge to an arbitrary value.'''
        self.set_value(labels, value)

    def get(self, labels):
        ''' Get gets the Gauge of an arbitrary group of labels'''
        return self.get_value(labels)

    def inc(self, labels):
        ''' Inc increments the Gauge by 1.'''
        self.add(labels, 1)

    def dec(self, labels):
        ''' Dec decrements the Gauge by 1.'''
        self.add(labels, -1)

    def add(self, labels, value):
        ''' Add adds the given value to the Gauge. (The value can be
            negative, resulting in a decrease of the Gauge.)
        '''
        try:
            current = self.get_value(labels)
        except KeyError:
            current = 0

        self.set_value(labels, current + value)

    def sub(self, labels, value):
        ''' Sub subtracts the given value from the Gauge. (The value can be
            negative, resulting in an increase of the Gauge.)
        '''
        self.add(labels, -value)


class Summary(Collector):
    '''
    A Summary captures individual observations from an event or sample stream
    and summarizes them in a manner similar to traditional summary statistics:

    1. sum of observations,
    2. observation count,
    3. rank estimations.

    Example use cases for Summaries:
    - Response latency
    - Request size
    '''

    kind = MetricsTypes.summary

    REPR_STR = "summary"
    DEFAULT_INVARIANTS = [(0.50, 0.05), (0.90, 0.01), (0.99, 0.001)]
    SUM_KEY = "sum"
    COUNT_KEY = "count"

    def __init__(self, name, doc, const_labels=None,
                 invariants=DEFAULT_INVARIANTS):
        super().__init__(name, doc, const_labels=const_labels)
        self.invariants = invariants

    def add(self, labels, value):
        ''' Add adds a single observation to the summary '''

        if type(value) not in (float, int):
            raise TypeError("Summary only works with digits (int, float)")

        try:
            e = self.get_value(labels)
        except KeyError:
            # Initialize quantile estimator
            e = quantile.Estimator(*self.invariants)
            self.set_value(labels, e)
        e.observe(float(value))

    def get(self, labels):
        '''
        Return a dict containing the sum, count and 0.5, 0.9 and 0.99
        percentiles.
        '''

        return_data = {}

        e = self.get_value(labels)

        # Set invariants data (default to 0.50, 0.90 and 0.99)
        for i in e._invariants:
            q = i._quantile
            return_data[q] = e.query(q)

        # Set sum and count
        return_data[self.SUM_KEY] = e._sum
        return_data[self.COUNT_KEY] = e._observations

        return return_data


class Histogram(Collector):
    '''
    A Histogram tracks the size and number of events in buckets.

    You can use Histograms for aggregatable calculation of quantiles.

    Example use cases:
    - Response latency
    - Request size
    '''

    kind = MetricsTypes.histogram

    REPR_STR = "histogram"
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25,
                       0.5, 1.0, 2.5, 5.0, 10.0, POS_INF)
    SUM_KEY = "sum"
    COUNT_KEY = "count"

    def __init__(self, name, doc, const_labels=None, buckets=DEFAULT_BUCKETS):
        super().__init__(name, doc, const_labels=const_labels)
        self.upper_bounds = buckets

    def add(self, labels, value):
        ''' Add adds a single observation to the histogram '''

        if type(value) not in (float, int):
            raise TypeError("Histogram only works with digits (int, float)")

        try:
            h = self.get_value(labels)
        except KeyError:
            # Initialize histogram aggregator
            h = histogram.Histogram(*self.upper_bounds)
            self.set_value(labels, h)
        h.observe(float(value))

    def get(self, labels):
        '''
        Return a dict containing the sum, count and buckets.
        '''

        return_data = {}

        h = self.get_value(labels)

        for upper_bound, cumulative_count in h.buckets.items():
            return_data[upper_bound] = cumulative_count

        # Set sum and count
        return_data[self.SUM_KEY] = h.sum
        return_data[self.COUNT_KEY] = h.observations

        return return_data
