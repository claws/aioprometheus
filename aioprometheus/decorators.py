'''
This module provides some convenience decorators for metrics
'''

import asyncio
import time

from .collectors import Counter, Gauge, Summary
from functools import wraps
from typing import Any, Callable, Dict


def timer(metric: Summary,
          labels: Dict[str, str] = None) -> Callable[..., Any]:
    '''
    This decorator provides a convenient way to time a callable.

    This decorator function wraps a function with code to calculate how long
    the wrapped function takes to execute and updates the metric with the
    duration.

    :param metric: a metric to update with the calculated function duration.
      The metric object being updated is expected to be a Summary metric
      object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a coroutine function that wraps the decortated function
    '''
    if not isinstance(metric, Summary):
        raise Exception(
            'timer decorator expects a Summary metric but got: {}'.format(
                metric))

    def measure(func):
        '''
        This function wraps a decorated callable with timing and metric
        updating logic.

        :param func: the callable to be timed.

        :returns: the return value from the decorated callable.
        '''
        @wraps(func)
        async def func_wrapper(*args, **kwds):
            start_time = time.monotonic()
            rv = func(*args, **kwds)
            if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                rv = await rv
            metric.add(labels, time.monotonic() - start_time)
            return rv

        return func_wrapper

    return measure


def inprogress(metric: Gauge,
               labels: Dict[str, str] = None) -> Callable[..., Any]:
    '''
    This decorator provides a convenient way to track in-progress requests
    (or other things) in a callable.

    This decorator function wraps a function with code to track how many
    of the measured items are in progress.

    The metric is incremented before calling the wrapped function and
    decremented when the wrapped function is complete.

    :param metric: a metric to increment and decrement. The metric object
      being updated is expected to be a Gauge metric object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a coroutine function that wraps the decortated function
    '''
    if not isinstance(metric, Gauge):
        raise Exception(
            'inprogess decorator expects a Gauge metric but got: {}'.format(
                metric))

    def track(func):
        '''
        This function wraps a decorated callable with metric incremeting
        and decrementing logic.

        :param func: the callable to be tracked.

        :returns: the return value from the decorated callable.
        '''
        @wraps(func)
        async def func_wrapper(*args, **kwds):
            metric.inc(labels)
            rv = func(*args, **kwds)
            if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                rv = await rv
            metric.dec(labels)
            return rv

        return func_wrapper

    return track


def count_exceptions(metric: Counter,
                     labels: Dict[str, str] = None) -> Callable[..., Any]:
    '''
    This decorator provides a convenient way to track count exceptions
    generated in a callable.

    This decorator function wraps a function with code to track how many
    exceptions occur.

    :param metric: a metric to increment when an exception is caught. The
      metric object being updated is expected to be a Counter metric object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a coroutine function that wraps the decortated function
    '''
    if not isinstance(metric, Counter):
        raise Exception(
            'count_exceptions decorator expects a Counter metric but got: {}'.format(
                metric))

    def track(func):
        '''
        This function wraps a decorated callable with metric incremeting
        logic.

        :param func: the callable to be tracked.

        :returns: the return value from the decorated callable.
        '''
        @wraps(func)
        async def func_wrapper(*args, **kwds):
            try:
                rv = func(*args, **kwds)
                if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                    rv = await rv
            except:
                metric.inc(labels)
                raise
            return rv

        return func_wrapper

    return track
