"""
This module holds common formatter type annotations.
"""

from typing import Dict, Tuple, Union

from aioprometheus.collectors import Counter, Gauge, Histogram, Summary

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
