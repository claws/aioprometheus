''' This module implements a Prometheus metrics text formatter '''

import collections

from .base import IFormatter
from ..collectors import Counter, Gauge, Summary, Histogram
from typing import cast, Callable, Dict, List, Tuple, Union

# imports only used for type annotations
from ..registry import CollectorRegistry

# typing aliases
LabelsType = Dict[str, str]
NumericValueType = Union[int, float]
# ValueType = Union[str, NumericValueType]
SummaryDictKeyType = Union[float, str]  # e.g. sum, 0.25, etc
SummaryDictType = Dict[SummaryDictKeyType, NumericValueType]
HistogramDictKeyType = Union[float, str]  # e.g. sum, 0.25, etc
HistogramDictType = Dict[HistogramDictKeyType, NumericValueType]
CollectorsType = Union[Counter, Gauge, Histogram, Summary]
MetricValueType = Union[NumericValueType, SummaryDictType, HistogramDictType]
MetricTupleType = Tuple[LabelsType, MetricValueType]
FormatterFuncType = Callable[[MetricTupleType, str, LabelsType], List[str]]


HELP_FMT = "# HELP {name} {doc}"
TYPE_FMT = "# TYPE {name} {kind}"
COMMENT_FMT = "# {comment}"
LABEL_FMT = "{key}=\"{value}\""
LABEL_SEPARATOR_FMT = ","
LINE_SEPARATOR_FMT = "\n"
METRIC_FMT = "{name}{labels} {value} {timestamp}"
POS_INF = float("inf")
NEG_INF = float("-inf")


class TextFormatter(IFormatter):
    ''' This formatter encodes into the Protocol Buffers binary format '''

    def __init__(self, timestamp: bool = False) -> None:
        ''' Initialise the text formatter.

        timestamp is a boolean, if you want timestamp in each metric.
        '''
        self.timestamp = timestamp
        self._headers = {
            'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'}

    def get_headers(self) -> Dict[str, str]:
        return self._headers

    def _format_line(self,
                     name: str,
                     labels: LabelsType,
                     value: NumericValueType,
                     const_labels: LabelsType = None) -> str:

        labels = self._unify_labels(labels, const_labels, True)

        labels_str = ""  # type: str
        if labels:
            _labels = [
                LABEL_FMT.format(key=k, value=v)
                for k, v in labels.items()]
            labels_str = LABEL_SEPARATOR_FMT.join(_labels)
            labels_str = "{{{labels}}}".format(labels=labels_str)

        ts = ""  # type: Union[str, int]
        if self.timestamp:
            ts = self._get_timestamp()

        result = METRIC_FMT.format(
            name=name, labels=labels_str, value=value, timestamp=ts)

        return result.strip()

    def _format_counter(self,
                        counter: MetricTupleType,
                        name: str,
                        const_labels: LabelsType) -> List[str]:
        '''
        :param counter: a 2-tuple containing labels and the counter value.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''
        labels, value = counter
        value = cast(NumericValueType, value)  # typing check, no runtime behaviour.
        line = self._format_line(name, labels, value, const_labels)
        return [line]

    def _format_gauge(self,
                      gauge: MetricTupleType,
                      name: str,
                      const_labels: LabelsType) -> List[str]:
        '''
        :param gauge: a 2-tuple containing labels and the gauge value.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''
        labels, value = gauge
        value = cast(NumericValueType, value)  # typing check, no runtime behaviour.
        line = self._format_line(name, labels, value, const_labels)
        return [line]

    def _format_summary(self,
                        summary: MetricTupleType,
                        name: str,
                        const_labels: LabelsType) -> List[str]:
        '''
        :param summary: a 2-tuple containing labels and a dict representing
          the summary value. The dict contains keys for each quantile as
          well as the sum and count fields.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''
        summary_labels, summary_value_dict = summary
        # typing check, no runtime behaviour.
        summary_value_dict = cast(SummaryDictType, summary_value_dict)
        results = []  # type: List[str]

        for k, v in summary_value_dict.items():
            # Start from a fresh dict for the labels (new or with preset data)
            labels = {}  # type: Dict[str, str]
            if summary_labels:
                labels = summary_labels.copy()

            # Quantiles need labels and not special name (like sum and count)
            if type(k) is not float:
                name_str = "{0}_{1}".format(name, k)
            else:
                labels['quantile'] = str(k)
                name_str = name
            results.append(
                self._format_line(name_str, labels, v, const_labels))

        return results

    def _format_histogram(self,
                          histogram: MetricTupleType,
                          name: str,
                          const_labels: LabelsType) -> List[str]:
        '''
        :param histogram: a 2-tuple containing labels and a dict representing
          the histogram value. The dict contains keys for each bucket as
          well as the sum and count fields.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''
        histogram_labels, histogram_value_dict = histogram
        # typing check, no runtime behaviour.
        histogram_value_dict = cast(HistogramDictType, histogram_value_dict)
        results = []  # type: List[str]

        for k, v in histogram_value_dict.items():
            # Stat from a fresh dict for the labels (new or with preset data)
            labels = {}  # type: Dict[str, str]
            if histogram_labels:
                labels = histogram_labels.copy()

            # Buckets need labels and not special name (like sum and count)
            if type(k) is not float:
                name_str = "{0}_{1}".format(name, k)
            else:
                upper_bound = k
                if upper_bound == POS_INF:
                    upper_bound = '+Inf'
                elif upper_bound == NEG_INF:
                    upper_bound = '-Inf'
                # Add the le ("less or equal") label.
                labels['le'] = str(upper_bound)
                # Use the special bucket label name
                name_str = name + '_bucket'
            results.append(
                self._format_line(name_str, labels, v, const_labels))

        return results

    def marshall_lines(self, collector: CollectorsType) -> List[str]:
        '''
        Marshalls a collector into a sequence of strings representing
        the metrics in the collector.

        :return: a list of strings.
        '''
        exec_method = None  # type: FormatterFuncType
        if isinstance(collector, Counter):
            exec_method = self._format_counter
        elif isinstance(collector, Gauge):
            exec_method = self._format_gauge
        elif isinstance(collector, Summary):
            exec_method = self._format_summary
        elif isinstance(collector, Histogram):
            exec_method = self._format_histogram
        else:
            raise TypeError("Not a valid object format")

        # create headers
        help_header = HELP_FMT.format(
            name=collector.name, doc=collector.doc)

        type_header = TYPE_FMT.format(
            name=collector.name, kind=collector.kind.name)

        # Prepare start headers
        lines = [help_header, type_header]

        for i in collector.get_all():
            i = cast(MetricTupleType, i)  # typing check, no runtime behaviour.
            r = exec_method(i, collector.name, collector.const_labels)
            lines.extend(r)

        return lines

    def marshall_collector(self, collector: CollectorsType) -> str:
        '''
        Marshalls a collector into a string containing one or more lines
        '''
        # need sort?
        result = sorted(self.marshall_lines(collector))
        return LINE_SEPARATOR_FMT.join(result)

    def marshall(self, registry: CollectorRegistry) -> bytes:
        ''' Marshalls a registry (containing collectors) into a bytes
        object '''

        blocks = []
        for i in registry.get_all():
            blocks.append(self.marshall_collector(i))

        # Sort? used in tests
        blocks = sorted(blocks)

        # Needs EOF
        blocks.append("")

        return LINE_SEPARATOR_FMT.join(blocks).encode('utf-8')
