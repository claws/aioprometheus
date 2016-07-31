
import abc
import collections
import datetime

from typing import Dict

# typing aliases
LabelsType = Dict[str, str]


class IFormatter(abc.ABC):

    @abc.abstractmethod
    def get_headers(self):
        ''' Returns a dict of headers for this response format '''

    @abc.abstractmethod
    def _format_counter(self, counter, name, const_labels):
        '''
        Returns a representation of a counter value in the implemented
        format.
        :param counter: a 2-tuple containing labels and the counter value.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''

    @abc.abstractmethod
    def _format_gauge(self, gauge, name, const_labels):
        '''
        Returns a representation of a gauge value in the implemented
        format.
        :param gauge: a 2-tuple containing labels and the gauge value.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''

    @abc.abstractmethod
    def _format_summary(self, summary, name, const_labels):
        '''
        Returns a representation of a summary value in the implemented
        format.

        :param summary: a 2-tuple containing labels and a dict representing
          the summary value. The dict contains keys for each quantile as
          well as the sum and count fields.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''

    @abc.abstractmethod
    def _format_histogram(self, histogram, name, const_labels):
        '''
        Returns a representation of a histogram value in the implemented
        format.

        :param histogram: a 2-tuple containing labels and a dict representing
          the histogram value. The dict contains keys for each bucket as
          well as the sum and count fields.
        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''

    @abc.abstractmethod
    def marshall(self, registry) -> bytes:
        ''' Marshalls a registry (containing many collectors) into a
        specific format.

        :returns: bytes
        '''

    def _unify_labels(self,
                      labels: LabelsType,
                      const_labels: LabelsType,
                      ordered: bool = False) -> LabelsType:
        '''
        Return a dict of all labels for a metric. This combines the explicit
        labels and any constant labels. If ordered is True then the labels
        are sorted by key.

        :param labels: a dict of labels for a metric.
        :param const_labels: a dict of constant labels to be associated with
          the metric.
        '''
        if const_labels:
            result = const_labels.copy()
            if labels:
                # Add labels to const labels
                for k, v in labels.items():
                    result[k] = v
        else:
            result = labels

        if ordered and result:
            result = collections.OrderedDict(
                sorted(result.items(), key=lambda t: t[0]))

        return result

    def _get_timestamp(self) -> int:
        '''
        Return a timestamp that can be used by a metric formatter.
        '''
        return int(
            datetime.datetime.now(
                tz=datetime.timezone.utc).timestamp() * 1000)
