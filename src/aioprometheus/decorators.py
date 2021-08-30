"""
This module provides some convenience decorators for metrics
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict

from .collectors import Counter, Gauge, Summary


def timer(metric: Summary, labels: Dict[str, str] = None) -> Callable[..., Any]:
    """
    This decorator wraps a callable with code to calculate how long the
    callable takes to execute and updates the metric with the duration.

    :param metric: a metric to update with the calculated function duration.
      The metric object must be a Summary metric object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a callable wrapping the decorated function. The callable will
      be awaitable if the wrapped function was a coroutine function.
    """
    if not isinstance(metric, Summary):
        raise Exception(f"timer decorator expects a Summary metric but got: {metric}")

    def measure(func):
        """
        This function wraps the callable with timing and metric updating logic.

        :param func: the callable to be timed.

        :returns: the return value from the decorated callable.
        """

        @wraps(func)
        async def async_func_wrapper(*args, **kwds):
            start_time = time.monotonic()
            rv = func(*args, **kwds)
            if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                try:
                    rv = await rv
                finally:
                    metric.add(labels, time.monotonic() - start_time)
            return rv

        @wraps(func)
        def func_wrapper(*args, **kwds):
            start_time = time.monotonic()
            try:
                rv = func(*args, **kwds)
            finally:
                metric.add(labels, time.monotonic() - start_time)
            return rv

        if asyncio.iscoroutinefunction(func):
            return async_func_wrapper
        return func_wrapper

    return measure


def inprogress(metric: Gauge, labels: Dict[str, str] = None) -> Callable[..., Any]:
    """
    This decorator wraps a callables with code to track whether it is currently
    in progress. The metric is incremented before calling the callable and is
    decremented when the callable is complete.

    :param metric: a metric to increment and decrement. The metric object
      must be a Gauge metric object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a callable wrapping the decorated function. The callable will
      be awaitable if the wrapped function was a coroutine function.
    """
    if not isinstance(metric, Gauge):
        raise Exception(f"inprogess decorator expects a Gauge metric but got: {metric}")

    def track(func):
        """
        This function wraps the callable with metric incremeting and
        decrementing logic.

        :param func: the callable to be tracked.

        :returns: the return value from the decorated callable.
        """

        @wraps(func)
        async def async_func_wrapper(*args, **kwds):
            metric.inc(labels)
            rv = func(*args, **kwds)
            if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                try:
                    rv = await rv
                finally:
                    metric.dec(labels)
            return rv

        @wraps(func)
        def func_wrapper(*args, **kwds):
            metric.inc(labels)
            try:
                rv = func(*args, **kwds)
            finally:
                metric.dec(labels)
            return rv

        if asyncio.iscoroutinefunction(func):
            return async_func_wrapper
        return func_wrapper

    return track


def count_exceptions(
    metric: Counter, labels: Dict[str, str] = None
) -> Callable[..., Any]:
    """
    This decorator wraps a callable with code to count how many times the
    callable generates an exception.

    :param metric: a metric to increment when an exception is caught. The
      metric object must be a Counter metric object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a callable wrapping the decorated function. The callable will
      be awaitable if the wrapped function was a coroutine function.
    """
    if not isinstance(metric, Counter):
        raise Exception(
            f"count_exceptions decorator expects a Counter metric but got: {metric}"
        )

    def track(func):
        """
        This function wraps the callable with metric incremeting logic.

        :param func: the callable to be monitored for exceptions.

        :returns: the return value from the decorated callable.
        """

        @wraps(func)
        async def async_func_wrapper(*args, **kwds):
            try:
                rv = func(*args, **kwds)
                if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                    rv = await rv
            except Exception:
                metric.inc(labels)
                raise
            return rv

        @wraps(func)
        def func_wrapper(*args, **kwds):
            try:
                rv = func(*args, **kwds)
            except Exception:
                metric.inc(labels)
                raise
            return rv

        if asyncio.iscoroutinefunction(func):
            return async_func_wrapper
        return func_wrapper

    return track
