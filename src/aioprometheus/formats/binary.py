"""
This module implements a formatter that emits metrics in a binary (Google
Protocol Buffers) format.
"""

from typing import Callable, Dict, List, Tuple, Union, cast

import prometheus_metrics_proto as pmp

# imports only used for type annotations
from aioprometheus.registry import CollectorRegistry

from ..collectors import Counter, Gauge, Histogram, Summary
from .base import IFormatter

# typing aliases
LabelsType = Dict[str, str]
NumericValueType = Union[int, float]
SummaryDictKeyType = Union[float, str]  # e.g. sum, 0.25, etc
SummaryDictType = Dict[SummaryDictKeyType, NumericValueType]
HistogramDictKeyType = Union[float, str]  # e.g. sum, 0.25, etc
HistogramDictType = Dict[HistogramDictKeyType, NumericValueType]
CollectorsType = Union[Counter, Gauge, Histogram, Summary]
MetricValueType = Union[float, SummaryDictType, HistogramDictType]
MetricTupleType = Tuple[LabelsType, MetricValueType]
FormatterFuncType = Callable[[MetricTupleType, str, LabelsType], pmp.Metric]


BINARY_CONTENT_TYPE = (
    "application/vnd.google.protobuf; "
    "proto=io.prometheus.client.MetricFamily; "
    "encoding=delimited"
)
BINARY_ACCEPTS = set(BINARY_CONTENT_TYPE.split("; "))


class BinaryFormatter(IFormatter):
    """This formatter encodes into the Protocol Buffers binary format"""

    def __init__(self, timestamp: bool = False) -> None:
        """
        :param timestamp: a boolean flag that when True will add a timestamp
          to metric.
        """
        self.timestamp = timestamp
        self._headers = {"Content-Type": BINARY_CONTENT_TYPE}

    def get_headers(self) -> Dict[str, str]:
        return self._headers

    def _format_counter(
        self, counter: MetricTupleType, name: str, const_labels: LabelsType
    ) -> pmp.Metric:
        """Create a Counter metric instance.

        :param counter: a 2-tuple containing labels and the counter value.
        :param name: the metric name.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        """
        counter_labels, counter_value = counter

        metric = pmp.utils.create_counter_metric(
            counter_labels,
            counter_value,
            timestamp=self.timestamp,
            const_labels=const_labels,
            ordered=True,
        )

        return metric

    def _format_gauge(
        self, gauge: MetricTupleType, name: str, const_labels: LabelsType
    ) -> pmp.Metric:
        """Create a Gauge metric instance.

        :param gauge: a 2-tuple containing labels and the gauge value.
        :param name: the metric name.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        """
        gauge_labels, gauge_value = gauge

        metric = pmp.utils.create_gauge_metric(
            gauge_labels,
            gauge_value,
            timestamp=self.timestamp,
            const_labels=const_labels,
            ordered=True,
        )

        return metric

    def _format_summary(
        self, summary: MetricTupleType, name: str, const_labels: LabelsType
    ) -> pmp.Metric:
        """Create a Summary metric instance.

        :param summary: a 2-tuple containing labels and a dict representing
          the summary value. The dict contains keys for each quantile as
          well as the sum and count fields.
        :param name: the metric name.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        """

        summary_labels, summary_value_dict = summary
        # typing check, no runtime behaviour.
        summary_value_dict = cast(SummaryDictType, summary_value_dict)

        metric = pmp.utils.create_summary_metric(
            summary_labels,
            summary_value_dict,
            samples_count=summary_value_dict["count"],
            samples_sum=summary_value_dict["sum"],
            timestamp=self.timestamp,
            const_labels=const_labels,
            ordered=True,
        )

        return metric

    def _format_histogram(
        self, histogram: MetricTupleType, name: str, const_labels: LabelsType
    ) -> pmp.Metric:
        """
        :param histogram: a 2-tuple containing labels and a dict representing
          the histogram value. The dict contains keys for each bucket as
          well as the sum and count fields.
        :param name: the metric name.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        """
        histogram_labels, histogram_value_dict = histogram
        # typing check, no runtime behaviour.
        histogram_value_dict = cast(HistogramDictType, histogram_value_dict)

        metric = pmp.utils.create_histogram_metric(
            histogram_labels,
            histogram_value_dict,
            samples_count=histogram_value_dict["count"],
            samples_sum=histogram_value_dict["sum"],
            timestamp=self.timestamp,
            const_labels=const_labels,
            ordered=True,
        )

        return metric

    def marshall_collector(self, collector: CollectorsType) -> pmp.MetricFamily:
        """
        Marshalls a collector into a :class:`MetricFamily` object representing
        the metrics in the collector.

        :return: a :class:`MetricFamily` object
        """
        exec_method = None  # type: FormatterFuncType
        if isinstance(collector, Counter):
            metric_type = pmp.COUNTER
            exec_method = self._format_counter
        elif isinstance(collector, Gauge):
            metric_type = pmp.GAUGE
            exec_method = self._format_gauge
        elif isinstance(collector, Summary):
            metric_type = pmp.SUMMARY
            exec_method = self._format_summary
        elif isinstance(collector, Histogram):
            metric_type = pmp.HISTOGRAM
            exec_method = self._format_histogram
        else:
            raise TypeError("Not a valid object format")

        metrics = []  # type: List[pmp.Metric]
        for i in collector.get_all():
            i = cast(MetricTupleType, i)  # typing check, no runtime behavior.
            r = exec_method(i, collector.name, collector.const_labels)
            metrics.append(r)

        mf = pmp.utils.create_metric_family(
            collector.name, collector.doc, metric_type, metrics
        )

        return mf

    def marshall(self, registry: CollectorRegistry) -> bytes:
        """Marshall the collectors in the registry into binary protocol
        buffer format.

        The Prometheus metrics parser expects each metric (MetricFamily) to
        be prefixed with a varint containing the size of the encoded metric.

        :returns: bytes
        """
        buf = bytearray()
        for i in registry.get_all():
            buf.extend(pmp.encode(self.marshall_collector(i)))
        return bytes(buf)
