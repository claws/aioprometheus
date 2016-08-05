
from aioprometheus import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    timer,
    inprogress,
    count_exceptions)
from aioprometheus.test_utils import AsyncioTestCase


class TestDecorators(AsyncioTestCase):

    async def test_timer(self):
        m = Summary('metric_label', 'metric help')

        # decorator should work methods as well as functions
        @timer(m, {'kind': 'function'})
        async def a():
            return

        await a()

        m_function = m.get({'kind': 'function'})
        self.assertEqual(m_function['count'], 1)

        # decorator should work methods as well as functions
        class B(object):

            @timer(m, {'kind': 'method'})
            async def b(self, arg1, arg2=None):
                return arg1 == 'b_arg', arg2 == 'arg_2'

        b = B()
        results = await b.b('b_arg', arg2='arg_2')
        self.assertTrue(all(results))

        m_method = m.get({'kind': 'method'})
        self.assertEqual(m_method['count'], 1)

        # Only Summary metric type can be used with @timer, others should
        # raise an exception.
        with self.assertRaises(Exception) as cm:
            m = Counter('metric_label', 'metric help')

            @timer(m)
            async def c():
                return
        self.assertIn(
            "timer decorator expects a Summary metric but got:",
            str(cm.exception))

    async def test_inprogress(self):
        m = Gauge('metric_label', 'metric help')

        # decorator should work methods as well as functions
        @inprogress(m, {'kind': 'function'})
        async def a():
            return

        await a()

        m_function_value = m.get({'kind': 'function'})
        self.assertEqual(m_function_value, 0)

        # decorator should work methods as well as functions
        class B(object):

            @inprogress(m, {'kind': 'method'})
            async def b(self, arg1, arg2=None):
                return arg1 == 'b_arg', arg2 == 'arg_2'

        b = B()
        results = await b.b('b_arg', arg2='arg_2')
        self.assertTrue(all(results))

        m_method_value = m.get({'kind': 'method'})
        self.assertEqual(m_method_value, 0)

        # Only Gauge metric type can be used with @timer, others should
        # raise an exception.
        with self.assertRaises(Exception) as cm:
            m = Counter('metric_label', 'metric help')

            @inprogress(m)
            async def c():
                return
        self.assertIn(
            "inprogess decorator expects a Gauge metric but got:",
            str(cm.exception))

    async def test_count_exceptions(self):
        m = Counter('metric_label', 'metric help')

        # decorator should work methods as well as functions
        @count_exceptions(m, {'kind': 'function'})
        async def a(raise_exc=False):
            if raise_exc:
                raise Exception('dummy exception')
            return

        await a()

        # metric should not exist until an exception occurs
        with self.assertRaises(KeyError):
            m.get({'kind': 'function'})

        with self.assertRaises(Exception) as cm:
            await a(True)
        self.assertIn("dummy exception", str(cm.exception))

        m_function_value = m.get({'kind': 'function'})
        self.assertEqual(m_function_value, 1)

        # decorator should work methods as well as functions
        class B(object):

            @count_exceptions(m, {'kind': 'method'})
            async def b(self, arg1, arg2=None, raise_exc=False):
                if raise_exc:
                    raise Exception('dummy exception')
                return arg1 == 'b_arg', arg2 == 'arg_2'

        b = B()

        results = await b.b('b_arg', arg2='arg_2')
        self.assertTrue(all(results))
        # metric should not exist until an exception occurs
        with self.assertRaises(KeyError):
            m.get({'kind': 'method'})

        with self.assertRaises(Exception) as cm:
            await b.b('b_arg', arg2='arg_2', raise_exc=True)
        self.assertIn("dummy exception", str(cm.exception))
        m_method_value = m.get({'kind': 'method'})
        self.assertEqual(m_method_value, 1)

        # Only Gauge metric type can be used with @timer, others should
        # raise an exception.
        with self.assertRaises(Exception) as cm:
            m = Histogram('metric_label', 'metric help')

            @count_exceptions(m)
            async def c():
                return
        self.assertIn(
            "count_exceptions decorator expects a Counter metric but got:",
            str(cm.exception))
