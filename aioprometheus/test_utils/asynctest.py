'''
This module is built upon the :mod:`unittest` standard library module.
It simplifies event loop related boilerplate code when testing code built
upon the :mod:`asyncio` standard library module.

This module imports the :mod:`unittest` package, overrides some of
its features and adds new ones.

Enhanced :class:`unittest.TestCase`:

- a new event loop is created at the beginning of each test. This event loop
  is set as the default event loop. The event loop is stopped, closed and
  destroyed at the end of each test.

- The :meth:`~TestCase.setUp()` and :meth:`~TestCase.tearDown()` methods can
  be coroutine functions.

- a test method in a TestCase (e.g. `test_*`) declared as a coroutine function
  or returning a coroutine will run in the event loop.

- cleanup functions registered with :meth:`~TestCase.addCleanup()` can be
  coroutine functions.


'''

import asyncio
import functools
import gc
import inspect
import sys
import unittest

if False:
    from asyncio.base_events import BaseEventLoop
    from asyncio.events import BaseDefaultEventLoopPolicy

PY34 = sys.version_info >= (3, 4)
PY35 = sys.version_info >= (3, 5)


def isawaitable(obj):
    ''' Return True if the object is an awaitable or is a function that
    returns an awaitable.

    This function is used internally by aiotesting.
    '''
    if PY35:
        result = inspect.iscoroutinefunction(obj) or inspect.isawaitable(obj)

    elif PY34:
        result = (isinstance(obj, asyncio.Future) or
                  asyncio.iscoroutine(obj) or
                  hasattr(obj, '__await__'))
    else:
        raise Exception(
            'isawaitable is not supported on Python {}'.format(
                sys.version_info))
    return result


class AsyncioTestCase(unittest.TestCase):
    '''
    This class enhances :class:`unittest.TestCase` to work nicely with
    tests that use the :mod:`asyncio` module.

    By default a new event loop is created for each test and is set as the
    default event loop. The setUp and tearDown methods can also be defined
    as coroutines.

    The behaviour of this class can be configured by defining some class
    attributes.

    There may be times when you need to run a specific event loop. This can
    be done by specifying a loop policy as a class attribute.

    .. code-block:: python

        from .my_code import MyEventLoopPolicy

        class MyEventLoop_TestCase(AsyncioTestCase):

            loop_policy = MyEventLoopPolicy()

    In a number of different situations it can be useful to have tests
    time-out after some reasonable period of time. Tests can sometimes
    stall the test suite progression by effectively hanging in the event
    loop while waiting for a future that never fires. For example, certain
    kinds of tests that rely on external processes or services and during
    early development of asynchronous test cases,

    With AsyncioTestCase you can use the ``@TestTimeout`` decorator on
    specific tests.

    .. code-block:: python

        class MyAsyncTestCase(AsyncioTestCase):

            @TestTimeout(3.0)
            def test_func(self):
                yield from asyncio.sleep(2.0)

    If :attr:`~aiotesting.AsyncioTestCase` is set to True then a class-wide
    timeout is used for each test in the TestCase. Alternatively, a class
    decorator can be used.

    .. code-block:: python

        @TestCaseTimeout(3.0)
        class MyAsyncTestCase(AsyncioTestCase):

            async def test_func(self):
                await asyncio.sleep(2.0)

    '''

    # A specific event loop can be used by defining an event loop policy.
    loop_policy = None  # type: BaseDefaultEventLoopPolicy

    loop = None  # type: BaseEventLoop

    # To stop poorly written tests from blocking the efficient progress
    # of running test cases, a default test timeout can be set. If you
    # need timeouts for specific tests then use the `@TestTimeout`
    # decorator..
    timeout = None  # type: float

    def run(self, result=None):
        '''
        Overrides the :meth:`~TestCase.run()` method so that
        :meth:`~TestCase.setUp()` and :meth:`~TestCase.tearDown()` can be
        coroutines.
        '''
        orig_result = result
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()

        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)
        if (getattr(self.__class__, "__unittest_skip__", False) or
                getattr(testMethod, "__unittest_skip__", False)):
            # If the class or method was skipped.
            try:
                skip_why = (
                    getattr(self.__class__, '__unittest_skip_why__', '') or
                    getattr(testMethod, '__unittest_skip_why__', ''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure = getattr(testMethod,
                                    "__unittest_expecting_failure__", False)
        outcome = unittest.case._Outcome(result)
        try:
            self._outcome = outcome

            with outcome.testPartExecutor(self):
                self._setUp()
            if outcome.success:
                outcome.expecting_failure = expecting_failure
                with outcome.testPartExecutor(self, isTest=True):
                    self._run_test_method(testMethod)
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    self._tearDown()

            self.doCleanups()
            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(
                            result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if orig_result is None:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome ->
            # outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None

    def addCleanup(self, function, *args, **kwargs):
        '''
        Add a function, with arguments, to be called when the test is
        completed. If function is a coroutine function, it will be run by the
        event loop before it is destroyed.
        '''
        if asyncio.iscoroutinefunction(function):
            return super().addCleanup(self.loop.run_until_complete,
                                      function(*args, **kwargs))

        return super().addCleanup(function, *args, **kwargs)

    def debug(self):
        '''Run the test without collecting errors in a TestResult'''
        self._setUp()
        meth = getattr(self, self._testMethodName)
        self._run_test_method(meth())
        self._tearDown()
        while self._cleanups:
            function, args, kwargs = self._cleanups.pop(-1)
            function(*args, **kwargs)

    # internals

    def _setUp(self):
        ''' Create a new loop for each test case '''
        asyncio.set_event_loop_policy(self.loop_policy)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        if asyncio.iscoroutinefunction(self.setUp):
            self.loop.run_until_complete(self.setUp())
        else:
            self.setUp()

    def _tearDown(self):
        ''' Destroy the event loop '''
        if asyncio.iscoroutinefunction(self.tearDown):
            self.loop.run_until_complete(self.tearDown())
        else:
            self.tearDown()

        if not isinstance(self.loop, asyncio.AbstractEventLoop):
            raise Exception('Invalid event loop: ', self.loop)
        if self.loop.is_running():
            self.loop.stop()
        self.loop.close()
        del self.loop
        asyncio.set_event_loop_policy(None)
        asyncio.set_event_loop(None)

        # By explicitly forcing a garbage collection here,
        # the event loop will report any remaining sockets
        # and coroutines left in the event loop which indicates
        # that further cleanup actions should be implemented
        # in the code under test.
        gc.collect()

    def _run_test_method(self, method):
        ''' Run a test method.

        If running the method returns an awaitable object then run it in the
        event loop.
        '''
        result = method()
        if isawaitable(result):
            if self.timeout:
                result = asyncio.wait_for(
                    result, timeout=self.timeout, loop=self.loop)
            self.loop.run_until_complete(result)


def TestCaseTimeout(timeout):
    '''
    This decorator function applies a default test timeout to the wrapped
    class. When the wrapped class is an AsyncTestCase class then the timeout
    attribute added to the class is used as the default timeout for all test
    methods within the TestCase.

    .. code-block:: python

        from aiotesting import AsyncioTestCase, TestCaseTimeout

        @TestCaseTimeout(1.0)
        class MyTestCase(AsyncioTestCase):

            async def test_func(self):
                await example_func()

    '''
    def wrapper(cls):
        cls.timeout = timeout
        return cls

    return wrapper


def TestTimeout(timeout):
    '''
    This decorator function applies a test timeout to a test method on a test
    by test basis.

    .. code-block:: python

        from aiotesting import AsyncioTestCase, TestTimeout

        class MyTestCase(AsyncioTestCase):

            @TestTimeout(1.0)
            async def test_func(self):
                await example_func()

    '''
    def decorating_function(user_function):

        def wrapper(*args, **kwargs):

            result = user_function(*args, **kwargs)

            if not isawaitable(result):
                raise Exception(
                    'Invalid use of TestTimeout decorator. Expected an '
                    'awaitable but got {}, type={}'.format(
                        result, type(result)))

            result = asyncio.wait_for(
                result, timeout=timeout, loop=asyncio.get_event_loop())

            return result

        return functools.update_wrapper(wrapper, user_function)

    return decorating_function
