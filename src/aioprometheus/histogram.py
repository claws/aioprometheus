from collections import OrderedDict
from typing import Dict, List, Union

POS_INF = float("inf")
NEG_INF = float("-inf")

# typing aliases
BucketType = float


def linearBuckets(
    start: Union[float, int], width: Union[int, float], count: int
) -> List[BucketType]:
    """Returns buckets that are spaced linearly.

    Returns ``count`` buckets, each ``width`` wide, where the lowest bucket
    has an upper bound of ``start``. There is no +Inf bucket is included in
    the returned list.

    :raises: Exception if ``count`` is zero or negative.
    """
    if count < 1:
        raise Exception("Invalid count, must be a positive number")
    return [start + i * width for i in range(count)]


def exponentialBuckets(
    start: Union[float, int], factor: Union[float, int], count: int
) -> List[BucketType]:
    """Returns buckets that are spaced exponentially.

    Returns ``count`` buckets, where the lowest bucket has an upper bound of
    ``start`` and each following bucket's upper bound is ``factor`` times the
    previous bucket's upper bound. There is no +Inf bucket is included in the
    returned list.

    :raises: Exception if ``count`` is 0 or negative.
    :raises: Exception if ``start`` is 0 or negative,
    :raises: Exception if ``factor`` is less than or equal 1.
    """

    if count < 1:
        raise Exception("Invalid count, must be a positive number")
    if start <= 0:
        raise Exception("Invalid start, must be positive")
    if factor < 1:
        raise Exception("Invalid factor, must be greater than one")
    return [start * (i * factor) for i in range(count)]


class Histogram(object):
    """
    A Histogram counts individual observations from an event into configurable
    buckets. This histogram implementation also provides a sum and count of
    observations.
    """

    def __init__(self, *buckets: BucketType) -> None:
        _buckets = [float(b) for b in buckets]

        if _buckets != sorted(buckets):
            raise ValueError("Buckets not in sorted order")

        if _buckets and _buckets[-1] != POS_INF:
            _buckets.append(POS_INF)

        if len(_buckets) < 2:
            raise ValueError("Must have at least two buckets")

        self.buckets = OrderedDict([(b, 0) for b in _buckets])  # type: Dict[float, int]
        self.observations = 0  # type: int
        self.sum = 0.0  # type: float

    def observe(self, value: Union[float, int]) -> None:
        """Observe the given amount.

        Observing a value into the histogram will cumulatively increment the
        count of observations for the buckets that the observed values falls
        within. It also adds the value to the sum of all observations.

        :param value: A metric value to add to the histogram.
        """
        for upper_bound in self.buckets:
            if value <= upper_bound:
                self.buckets[upper_bound] += 1
        self.sum += value
        self.observations += 1
