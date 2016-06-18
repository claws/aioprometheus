
from collections import OrderedDict

POS_INF = float("inf")
NEG_INF = float("-inf")


def linearBuckets(start, width, count):
    '''
    Returns 'count' buckets, each 'width' wide, where the lowest bucket has an
    upper bound of 'start'. No +Inf bucket is included in the returned list.

    Raises exception if 'count' is zero or negative.
    '''
    if count < 1:
        raise Exception('Invalid count, must be a positive number')
    return [start + i * width for i in range(count)]


def exponentialBuckets(start, factor, count):
    '''
    Returns 'count' buckets, where the lowest bucket has an upper bound of
    'start' and each following bucket's upper bound is 'factor' times the
    previous bucket's upper bound. No +Inf bucket is included in the returned
    list.

    Raises exception if 'count' is 0 or negative, if 'start' is 0 or negative,
    or if 'factor' is less than or equal 1.
    '''

    if count < 1:
        raise Exception('Invalid count, must be a positive number')
    if start <= 0:
        raise Exception('Invalid start, must be positive')
    if factor < 1:
        raise Exception('Invalid factor, must be greater than one')
    return [start * (i * factor) for i in range(count)]


class Histogram(object):
    '''
    A Histogram counts individual observations from an event into configurable
    buckets. This histogram implementation also provides a sum and count of
    observations.
    '''

    def __init__(self, *buckets):
        buckets = [float(b) for b in buckets]

        if buckets != sorted(buckets):
            raise ValueError('Buckets not in sorted order')

        if buckets and buckets[-1] != POS_INF:
            buckets.append(POS_INF)

        if len(buckets) < 2:
            raise ValueError('Must have at least two buckets')

        self.buckets = OrderedDict([(b, 0) for b in buckets])
        self.observations = 0
        self.sum = 0

    def observe(self, value):
        ''' Observe the given amount.

        Increment the count of observations, add value to the sum and
        increment the appropriate bucket counter.
        '''
        # The last bucket is +Inf, so we will always increment.
        for upper_bound in self.buckets:
            if value <= upper_bound:
                self.buckets[upper_bound] += 1
                break
        self.sum += value
        self.observations += 1
