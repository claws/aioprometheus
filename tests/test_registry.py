import unittest

from aioprometheus import (
    CollectorRegistry,
    Collector,
    Counter,
    Gauge,
    Summary)


class TestRegistry(unittest.TestCase):

    def setUp(self):
        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }

    def test_register(self):
        ''' check collectors can be registered '''

        q = 100
        collectors = [
            Collector('test' + str(i), 'Test' + str(i)) for i in range(q)]

        r = CollectorRegistry()

        for i in collectors:
            r.register(i)

        self.assertEqual(q, len(r.collectors))

    def test_register_sames(self):
        ''' check registering same metrics raises exceptoion '''
        r = CollectorRegistry()

        r.register(Collector(**self.data))

        with self.assertRaises(ValueError) as context:
            r.register(Collector(**self.data))

        self.assertEqual(
            "Collector {} is already registered".format(self.data['name']),
            str(context.exception))

    def test_register_counter(self):
        ''' check registering a counter collector '''
        r = CollectorRegistry()
        r.register(Counter(**self.data))

        self.assertEqual(1, len(r.collectors))

    def test_register_gauge(self):
        ''' check registering a gauge collector '''
        r = CollectorRegistry()
        r.register(Gauge(**self.data))

        self.assertEqual(1, len(r.collectors))

    def test_register_summary(self):
        ''' check registering a summary collector '''
        r = CollectorRegistry()
        r.register(Summary(**self.data))

        self.assertEqual(1, len(r.collectors))

    def test_register_wrong_type(self):
        ''' check registering an invalid collector raises an exception '''
        r = CollectorRegistry()

        with self.assertRaises(TypeError) as context:
            r.register("This will fail")
        self.assertIn(
            "Invalid collector type: ",
            str(context.exception))

    def test_deregister(self):
        ''' check collectors can be deregistered '''
        r = CollectorRegistry()
        r.register(Collector(**self.data))

        r.deregister(self.data['name'])

        self.assertEqual(0, len(r.collectors))

    def test_get(self):
        r = CollectorRegistry()
        c = Collector(**self.data)
        r.register(c)

        self.assertEqual(c, r.get(c.name))

    def test_get_all(self):
        q = 100
        collectors = [
            Collector('test' + str(i), 'Test' + str(i)) for i in range(q)]

        r = CollectorRegistry()

        for i in collectors:
            r.register(i)

        result = r.get_all()

        self.assertTrue(isinstance(result, list))
        self.assertEqual(q, len(result))
