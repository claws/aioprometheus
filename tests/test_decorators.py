import asyncio

import asynctest

from aioprometheus import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Summary,
    count_exceptions,
    inprogress,
    timer,
)


class TestDecorators(asynctest.TestCase):
    def tearDown(self):
        REGISTRY.clear()

    async def test_timer(self):
        """check timer decorator behaviour"""

        m = Summary("metric_label", "metric help")

        # decorator should work with async functions
        @timer(m, {"kind": "async_function"})
        async def async_f(should_raise: bool):
            if should_raise:
                raise Exception("Boom")

        # decorator should work with regular functions too
        @timer(m, {"kind": "regular_function"})
        def regular_f(should_raise: bool):
            if should_raise:
                raise Exception("Boom")

        # decorator should work with methods too
        class B:
            @timer(m, {"kind": "async_method"})
            async def b(self, should_raise: bool, arg_1, kwarg_1=None):
                if should_raise:
                    raise Exception("Boom")
                return arg_1 == "b_arg", kwarg_1 == "kwarg_1"

        b = B()

        SUB_TESTS = (
            ("Normal test", False, 1),
            ("Exception test", True, 2),
        )
        for test_msg, raises, count in SUB_TESTS:
            with self.subTest(test_msg, raises=raises):

                if raises:
                    # check decorator with async function
                    with self.assertRaises(Exception) as cm:
                        await async_f(raises)

                    # check decorator with regular function
                    with self.assertRaises(Exception) as cm:
                        regular_f(raises)

                    # check decorator with methods too
                    with self.assertRaises(Exception) as cm:
                        await b.b(raises, "b_arg", kwarg_1="kwarg_1")

                else:
                    # check decorator with async function
                    await async_f(raises)

                    # check decorator with regular function
                    regular_f(raises)

                    # check decorator with methods too
                    results = await b.b(raises, "b_arg", kwarg_1="kwarg_1")
                    self.assertTrue(all(results))

                # check async function updated metric
                m_async_function_value = m.get({"kind": "async_function"})
                self.assertEqual(m_async_function_value["count"], count)

                # check regular function updated metric
                m_regular_function_value = m.get({"kind": "regular_function"})
                self.assertEqual(m_regular_function_value["count"], count)

                # check async method updated metric
                m_method_value = m.get({"kind": "async_method"})
                self.assertEqual(m_method_value["count"], count)

    async def test_timer_with_non_summary_metric(self):
        """check only summary metric can be used with timer decorator"""
        with self.assertRaises(Exception) as cm:
            m = Counter("metric_label", "metric help")

            @timer(m)
            async def c():
                return

        self.assertIn(
            "timer decorator expects a Summary metric but got:", str(cm.exception)
        )

    async def test_inprogress(self):
        """check inprogress decorator behaviour"""
        m = Gauge("metric_label", "metric help")

        # decorator should work with async functions
        @inprogress(m, {"kind": "async_function"})
        async def async_f(should_raise: bool = False, duration: float = 0.0):
            if should_raise:
                raise Exception("Boom")
            else:
                await asyncio.sleep(duration)

        # decorator should work with regular functions too
        @inprogress(m, {"kind": "regular_function"})
        def regular_f(should_raise: bool):
            if should_raise:
                raise Exception("Boom")

        # decorator should work with methods too
        class B(object):
            @inprogress(m, {"kind": "method"})
            async def b(self, should_raise: bool, arg_1, kwarg_1=None):
                if should_raise:
                    raise Exception("Boom")
                return arg_1 == "b_arg", kwarg_1 == "kwarg_1"

        b = B()

        SUB_TESTS = (
            ("Normal test", False),
            ("Exception test", True),
        )
        for test_msg, raises in SUB_TESTS:
            with self.subTest(test_msg, raises=raises):

                if raises:
                    # check decorator with async function
                    with self.assertRaises(Exception) as cm:
                        await async_f(raises)

                    # check decorator with regular function
                    with self.assertRaises(Exception) as cm:
                        regular_f(raises)

                    # check decorator with methods too
                    with self.assertRaises(Exception) as cm:
                        await b.b(raises, "b_arg", kwarg_1="kwarg_1")

                else:

                    # check decorator with async function.
                    # Set a non-zero wait duration so we can check that the
                    # metric actually increases while it is in-progress
                    f = asyncio.ensure_future(async_f(raises, duration=0.1))

                    # yield to the event loop briefly so that the coroutine can start
                    await asyncio.sleep(0.0)

                    # check that the inprogress metric has incremented
                    m_async_function_value = m.get({"kind": "async_function"})
                    self.assertEqual(m_async_function_value, 1)

                    # wait for the coroutine to complete so we can check that the
                    # in-progress state has returned to zero.
                    await f

                    # check decorator with regular function
                    regular_f(raises)

                    # check decorator with methods too
                    results = await b.b(raises, "b_arg", kwarg_1="kwarg_1")
                    self.assertTrue(all(results))

                m_async_function_value = m.get({"kind": "async_function"})
                self.assertEqual(m_async_function_value, 0)

                m_regular_function_value = m.get({"kind": "regular_function"})
                self.assertEqual(m_regular_function_value, 0)

                m_method_value = m.get({"kind": "method"})
                self.assertEqual(m_method_value, 0)

    async def test_inprogress_with_non_gauge_metric(self):
        """check only gauge metrics can be used with inprogress decorator"""
        with self.assertRaises(Exception) as cm:
            m = Counter("metric_label", "metric help")

            @inprogress(m)
            async def c():
                return

        self.assertIn(
            "inprogess decorator expects a Gauge metric but got:", str(cm.exception)
        )

    async def test_count_exceptions(self):
        """check count exceptions decorator behaviour"""
        m = Counter("metric_label", "metric help")

        # decorator should work with async functions
        @count_exceptions(m, {"kind": "async_function"})
        async def async_f(should_raise: bool):
            if should_raise:
                raise Exception("Boom")

        # decorator should work with regular functions too
        @count_exceptions(m, {"kind": "regular_function"})
        def regular_f(should_raise: bool):
            if should_raise:
                raise Exception("Boom")

        # decorator should work with methods too
        class B:
            @count_exceptions(m, {"kind": "async_method"})
            async def b(self, should_raise: bool, arg_1, kwarg_1=None):
                if should_raise:
                    raise Exception("Boom")
                return arg_1 == "b_arg", kwarg_1 == "kwarg_1"

        b = B()

        SUB_TESTS = (
            ("Normal test", False),
            ("Exception test", True),
        )
        for test_msg, raises in SUB_TESTS:
            with self.subTest(test_msg, raises=raises):

                if raises:
                    # check decorator with async function
                    with self.assertRaises(Exception) as cm:
                        await async_f(raises)

                    # check async function updated metric
                    m_async_function_value = m.get({"kind": "async_function"})
                    self.assertEqual(m_async_function_value, 1)

                    # check decorator with regular function
                    with self.assertRaises(Exception) as cm:
                        regular_f(raises)

                    # check regular function updated metric
                    m_regular_function_value = m.get({"kind": "regular_function"})
                    self.assertEqual(m_regular_function_value, 1)

                    # check decorator with methods too
                    with self.assertRaises(Exception) as cm:
                        await b.b(raises, "b_arg", kwarg_1="kwarg_1")
                        results = await b.b(raises, "b_arg", kwarg_1="kwarg_1")

                    # check async method updated metric
                    m_method_value = m.get({"kind": "async_method"})
                    self.assertEqual(m_method_value, 1)

                else:
                    # check decorator with async function
                    await async_f(raises)

                    # metric should not exist until an exception occurs
                    with self.assertRaises(Exception) as cm:
                        m.get({"kind": "async_function"})

                    # check decorator with regular function
                    regular_f(raises)

                    # metric should not exist until an exception occurs
                    with self.assertRaises(Exception) as cm:
                        m.get({"kind": "regular_function"})

                    # check decorator with methods too
                    results = await b.b(raises, "b_arg", kwarg_1="kwarg_1")
                    self.assertTrue(all(results))

                    # metric should not exist until an exception occurs
                    with self.assertRaises(Exception) as cm:
                        m.get({"kind": "async_method"})

    async def test_count_exceptions_with_non_counter_metric(self):
        """check only counter metrics can be used with count exceptions decorator"""
        with self.assertRaises(Exception) as cm:
            m = Histogram("metric_label", "metric help")

            @count_exceptions(m)
            async def c():
                return

        self.assertIn(
            "count_exceptions decorator expects a Counter metric but got:",
            str(cm.exception),
        )
