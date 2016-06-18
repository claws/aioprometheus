
import unittest

from aioprometheus import (
    Collector,
    Counter,
    Gauge,
    Histogram,
    Registry,
    Summary)


class TestCollectorDict(unittest.TestCase):

    def setUp(self):
        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }

        self.c = Collector(**self.data)

    def test_initialization(self):
        self.assertEqual(self.data['name'], self.c.name)
        self.assertEqual(self.data['doc'], self.c.doc)
        self.assertEqual(self.data['const_labels'], self.c.const_labels)

    def test_set_value(self):
        data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
        )

        for m in data:
            self.c.set_value(m[0], m[1])

        self.assertEqual(len(data), len(self.c.values))

    def test_same_value(self):
        data = (
            ({'country': "sp", "device": "desktop", "ts": "GMT+1"}, 520),
            ({"ts": "GMT+1", 'country': "sp", "device": "desktop"}, 521),
            ({'country': "sp", "ts": "GMT+1", "device": "desktop"}, 522),
            ({"device": "desktop", "ts": "GMT+1", 'country': "sp"}, 523),
        )

        for m in data:
            self.c.set_value(m[0], m[1])

        self.assertEqual(1, len(self.c.values))
        self.assertEqual(523, self.c.values[data[0][0]])

    def test_get_value(self):
        data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
        )

        for m in data:
            self.c.set_value(m[0], m[1])

        for m in data:
            self.assertEqual(m[1], self.c.get_value(m[0]))

    def test_not_const_labels(self):
        del self.data['const_labels']
        self.c = Collector(**self.data)

    def test_not_name(self):
        with self.assertRaises(TypeError) as context:
            del self.data['name']
            self.c = Collector(**self.data)

        self.assertEqual(
            "__init__() missing 1 required positional argument: 'name'",
            str(context.exception))

    def test_not_help_text(self):
        with self.assertRaises(TypeError) as context:
            del self.data['doc']
            self.c = Collector(**self.data)

        self.assertEqual(
            "__init__() missing 1 required positional argument: 'doc'",
            str(context.exception))

    def test_without_labels(self):
        data = (
            ({}, 520),
            (None, 654),
            ("", 1001),
        )

        for i in data:
            self.c.set_value(i[0], i[1])

        self.assertEqual(1, len(self.c.values))
        self.assertEqual((data)[len(data) - 1][1], self.c.values[data[0][0]])

    def test_wrong_labels(self):

        # Normal set
        with self.assertRaises(ValueError) as context:
            self.c.set_value({'job': 1, 'ok': 2}, 1)

        self.assertEqual('Invalid label name: job', str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.c.set_value({'__not_ok': 1, 'ok': 2}, 1)

        self.assertEqual('Invalid label prefix: __not_ok', str(context.exception))

        # Constructor set
        with self.assertRaises(ValueError) as context:
            Collector("x", "y", {'job': 1, 'ok': 2})

        self.assertEqual('Invalid label name: job', str(context.exception))

        with self.assertRaises(ValueError) as context:
            Collector("x", "y", {'__not_ok': 1, 'ok': 2})

        self.assertEqual('Invalid label prefix: __not_ok', str(context.exception))

    def test_get_all(self):
        data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
            ({'country': "ch", "device": "mobile"}, 654),
            ({'country': "ca", "device": "desktop"}, 1001),
            ({'country': "jp", "device": "desktop"}, 995),
            ({'country': "au", "device": "desktop"}, 520),
            ({'country': "py", "device": "mobile"}, 654),
            ({'country': "ar", "device": "desktop"}, 1001),
            ({'country': "pt", "device": "desktop"}, 995),
        )

        for i in data:
            self.c.set_value(i[0], i[1])

        def country_fetcher(x):
            return x[0]['country']
        sorted_data = sorted(data, key=country_fetcher)
        sorted_result = sorted(self.c.get_all(), key=country_fetcher)
        self.assertEqual(sorted_data, sorted_result)


class TestCounter(unittest.TestCase):

    def setUp(self):
        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }

        self.c = Counter(**self.data)

    def test_set(self):

        data = (
            {
                'labels': {'country': "sp", "device": "desktop"},
                'values': range(10)
            },
            {
                'labels': {'country': "us", "device": "mobile"},
                'values': range(10, 20)
            },
            {
                'labels': {'country': "uk", "device": "desktop"},
                'values': range(20, 30)
            }
        )

        for i in data:
            for j in i['values']:
                self.c.set(i['labels'], j)

        self.assertEqual(len(data), len(self.c.values))

    def test_get(self):
        data = (
            {
                'labels': {'country': "sp", "device": "desktop"},
                'values': range(10)
            },
            {
                'labels': {'country': "us", "device": "mobile"},
                'values': range(10, 20)
            },
            {
                'labels': {'country': "uk", "device": "desktop"},
                'values': range(20, 30)
            }
        )

        for i in data:
            for j in i['values']:
                self.c.set(i['labels'], j)
                self.assertEqual(j, self.c.get(i['labels']))

        # Last check
        for i in data:
            self.assertEqual(max(i['values']), self.c.get(i['labels']))

    def test_set_get_without_labels(self):
        data = {
            'labels': {},
            'values': range(100)
        }

        for i in data['values']:
            self.c.set(data['labels'], i)

        self.assertEqual(1, len(self.c.values))

        self.assertEqual(max(data['values']), self.c.get(data['labels']))

    def test_inc(self):
        iterations = 100
        labels = {'country': "sp", "device": "desktop"}

        for i in range(iterations):
            self.c.inc(labels)

        self.assertEqual(iterations, self.c.get(labels))

    def test_add(self):
        labels = {'country': "sp", "device": "desktop"}
        iterations = 100

        for i in range(iterations):
            self.c.add(labels, i)

        self.assertEqual(sum(range(iterations)), self.c.get(labels))

    def test_negative_add(self):
        labels = {'country': "sp", "device": "desktop"}

        with self.assertRaises(ValueError) as context:
            self.c.add(labels, -1)
        self.assertEqual('Counters can\'t decrease', str(context.exception))


class TestGauge(unittest.TestCase):

    def setUp(self):
        self.data = {
            'name': "hdd_disk_used",
            'doc': "Disk space used",
            'const_labels': {"server": "1.db.production.my-app"},
        }

        self.g = Gauge(**self.data)

    def test_set(self):
        data = (
            {
                'labels': {'max': "500G", 'dev': "sda"},
                'values': range(0, 500, 50)
            },
            {
                'labels': {'max': "1T", 'dev': "sdb"},
                'values': range(0, 1000, 100)
            },
            {
                'labels': {'max': "10T", 'dev': "sdc"},
                'values': range(0, 10000, 1000)
            }
        )

        for i in data:
            for j in i['values']:
                self.g.set(i['labels'], j)

        self.assertEqual(len(data), len(self.g.values))

    def test_get(self):
        data = (
            {
                'labels': {'max': "500G", 'dev': "sda"},
                'values': range(0, 500, 50)
            },
            {
                'labels': {'max': "1T", 'dev': "sdb"},
                'values': range(0, 1000, 100)
            },
            {
                'labels': {'max': "10T", 'dev': "sdc"},
                'values': range(0, 10000, 1000)
            }
        )

        for i in data:
            for j in i['values']:
                self.g.set(i['labels'], j)
                self.assertEqual(j, self.g.get(i['labels']))

        for i in data:
            self.assertEqual(max(i['values']), self.g.get(i['labels']))

    def test_set_get_without_labels(self):
        data = {
            'labels': {},
            'values': range(100)
        }

        for i in data['values']:
            self.g.set(data['labels'], i)

        self.assertEqual(1, len(self.g.values))

        self.assertEqual(max(data['values']), self.g.get(data['labels']))

    def test_inc(self):
        iterations = 100
        labels = {'max': "10T", 'dev': "sdc"}

        for i in range(iterations):
            self.g.inc(labels)
            self.assertEqual(i + 1, self.g.get(labels))

        self.assertEqual(iterations, self.g.get(labels))

    def test_dec(self):
        iterations = 100
        labels = {'max': "10T", 'dev': "sdc"}
        self.g.set(labels, iterations)

        for i in range(iterations):
            self.g.dec(labels)
            self.assertEqual(iterations - (i + 1), self.g.get(labels))

        self.assertEqual(0, self.g.get(labels))

    def test_add(self):
        iterations = 100
        labels = {'max': "10T", 'dev': "sdc"}

        for i in range(iterations):
            self.g.add(labels, i)

        self.assertEqual(sum(range(iterations)), self.g.get(labels))

    def test_add_negative(self):
        iterations = 100
        labels = {'max': "10T", 'dev': "sdc"}

        for i in range(iterations):
            self.g.add(labels, -i)

        self.assertEqual(sum(map(lambda x: -x, range(iterations))),
                         self.g.get(labels))

    def test_sub(self):
        iterations = 100
        labels = {'max': "10T", 'dev': "sdc"}

        for i in range(iterations):
            self.g.sub(labels, i)

        self.assertEqual(sum(map(lambda x: -x, range(iterations))),
                         self.g.get(labels))

    def test_sub_positive(self):
        iterations = 100
        labels = {'max': "10T", 'dev': "sdc"}

        for i in range(iterations):
            self.g.sub(labels, -i)

        self.assertEqual(sum(range(iterations)), self.g.get(labels))


class TestSummary(unittest.TestCase):

    def setUp(self):
        self.data = {
            'name': "http_request_duration_microseconds",
            'doc': "Request duration per application",
            'const_labels': {"app": "my_app"},
        }

        self.s = Summary(**self.data)

    def test_add(self):
        data = (
            {
                'labels': {'handler': '/static'},
                'values': range(0, 500, 50)
            },
            {
                'labels': {'handler': '/p'},
                'values': range(0, 1000, 100)
            },
            {
                'labels': {'handler': '/p/login'},
                'values': range(0, 10000, 1000)
            }
        )

        for i in data:
            for j in i['values']:
                self.s.add(i['labels'], j)

        for i in data:
            self.assertEqual(len(i['values']),
                             self.s.values[i['labels']]._observations)

    def test_get(self):
        labels = {'handler': '/static'}
        values = [3, 5.2, 13, 4]

        for i in values:
                self.s.add(labels, i)

        data = self.s.get(labels)
        correct_data = {
            'sum': 25.2,
            'count': 4,
            0.50: 4.0,
            0.90: 5.2,
            0.99: 5.2,
        }

        self.assertEqual(correct_data, data)

    def test_add_get_without_labels(self):
        labels = None
        values = [3, 5.2, 13, 4]

        for i in values:
            self.s.add(labels, i)

        self.assertEqual(1, len(self.s.values))

        correct_data = {
            'sum': 25.2,
            'count': 4,
            0.50: 4.0,
            0.90: 5.2,
            0.99: 5.2,
        }
        self.assertEqual(correct_data, self.s.get(labels))

    def test_add_wrong_types(self):
        labels = None
        values = ["3", (1, 2), {'1': 2}, True]

        for i in values:
            with self.assertRaises(TypeError) as context:
                self.s.add(labels, i)
        self.assertEqual("Summary only works with digits (int, float)",
                         str(context.exception))


class TestHistogram(unittest.TestCase):

    def setUp(self):
        self.data = {
            'name': "http_request_duration_microseconds",
            'doc': "Request duration per application",
            'const_labels': {"app": "my_app"},
        }

        self.h = Histogram(**self.data)

    def test_wrong_labels(self):

        with self.assertRaises(ValueError) as context:
            self.h.set_value({'le': 2}, 1)

        self.assertEqual('Invalid label name: le', str(context.exception))
