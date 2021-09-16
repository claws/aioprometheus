"""
This module holds common formatter type annotations.
"""
from typing import Dict, Tuple, Union

import quantile

from aioprometheus import histogram

LabelsType = Dict[str, str]
NumericValueType = Union[int, float, histogram.Histogram, quantile.Estimator]
ValueType = Union[str, NumericValueType]

SummaryDictKeyType = Union[float, str]  # e.g. sum, 0.25, etc
SummaryDictType = Dict[SummaryDictKeyType, NumericValueType]

HistogramDictKeyType = Union[float, str]  # e.g. sum, 0.25, etc
HistogramDictType = Dict[HistogramDictKeyType, Union[int, float]]

MetricValueType = Union[NumericValueType, SummaryDictType, HistogramDictType]
MetricTupleType = Tuple[LabelsType, MetricValueType]
