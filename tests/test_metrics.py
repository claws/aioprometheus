import unittest

from aioprometheus.collectors import (
    REGISTRY,
    Collector,
    Counter,
    Gauge,
    Histogram,
    Summary,
)

POS_INF = float("inf")
NEG_INF = float("-inf")


class TestCollectorBase(unittest.TestCase):
    def setUp(self):
        self.default_data = {
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {"app": "my_app"},
        }

    def tearDown(self):
        REGISTRY.clear()

    def test_initialization(self):
        c = Collector(**self.default_data)
        self.assertEqual(self.default_data["name"], c.name)
        self.assertEqual(self.default_data["doc"], c.doc)
        self.assertEqual(self.default_data["const_labels"], c.const_labels)

        # check metrics automatically got registered
        collector_name = self.default_data["name"]
        self.assertIn(collector_name, REGISTRY.collectors)

    def test_set_value(self):
        c = Collector(**self.default_data)

        data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
        )

        for m in data:
            c.set_value(m[0], m[1])

        self.assertEqual(len(data), len(c.values))

    def test_same_value(self):
        c = Collector(**self.default_data)

        data = (
            ({"country": "sp", "device": "desktop", "ts": "GMT+1"}, 520),
            ({"ts": "GMT+1", "country": "sp", "device": "desktop"}, 521),
            ({"country": "sp", "ts": "GMT+1", "device": "desktop"}, 522),
            ({"device": "desktop", "ts": "GMT+1", "country": "sp"}, 523),
        )

        for m in data:
            c.set_value(m[0], m[1])

        self.assertEqual(1, len(c.values))
        self.assertEqual(523, c.values[data[0][0]])

    def test_get_value(self):
        c = Collector(**self.default_data)
        data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
        )

        for m in data:
            c.set_value(m[0], m[1])

        for m in data:
            self.assertEqual(m[1], c.get_value(m[0]))

    def test_not_const_labels(self):
        del self.default_data["const_labels"]
        c = Collector(**self.default_data)

    def test_not_name(self):
        with self.assertRaises(TypeError) as context:
            del self.default_data["name"]
            c = Collector(**self.default_data)

        self.assertIn(
            "__init__() missing 1 required positional argument: 'name'",
            str(context.exception),
        )

    def test_not_help_text(self):
        with self.assertRaises(TypeError) as context:
            del self.default_data["doc"]
            c = Collector(**self.default_data)

        self.assertIn(
            "__init__() missing 1 required positional argument: 'doc'",
            str(context.exception),
        )

    def test_without_labels(self):
        c = Collector(**self.default_data)
        data = (({}, 520), (None, 654), ("", 1001))

        for i in data:
            c.set_value(i[0], i[1])

        self.assertEqual(1, len(c.values))
        self.assertEqual((data)[len(data) - 1][1], c.values[data[0][0]])

    def test_wrong_labels(self):
        c = Collector(**self.default_data)

        # Normal set
        with self.assertRaises(ValueError) as context:
            c.set_value({"job": 1, "ok": 2}, 1)

        self.assertEqual("Invalid label name: job", str(context.exception))

        with self.assertRaises(ValueError) as context:
            c.set_value({"__not_ok": 1, "ok": 2}, 1)

        self.assertEqual("Invalid label prefix: __not_ok", str(context.exception))

        # Constructor set
        with self.assertRaises(ValueError) as context:
            Collector("x", "y", {"job": 1, "ok": 2})

        self.assertEqual("Invalid label name: job", str(context.exception))

        with self.assertRaises(ValueError) as context:
            Collector("x", "y", {"__not_ok": 1, "ok": 2})

        self.assertEqual("Invalid label prefix: __not_ok", str(context.exception))

    def test_get_all(self):
        c = Collector(**self.default_data)
        data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
            ({"country": "ch", "device": "mobile"}, 654),
            ({"country": "ca", "device": "desktop"}, 1001),
            ({"country": "jp", "device": "desktop"}, 995),
            ({"country": "au", "device": "desktop"}, 520),
            ({"country": "py", "device": "mobile"}, 654),
            ({"country": "ar", "device": "desktop"}, 1001),
            ({"country": "pt", "device": "desktop"}, 995),
        )

        for i in data:
            c.set_value(i[0], i[1])

        def country_fetcher(x):
            return x[0]["country"]

        sorted_data = sorted(data, key=country_fetcher)
        sorted_result = sorted(c.get_all(), key=country_fetcher)
        self.assertEqual(sorted_data, sorted_result)


class TestCounterMetric(unittest.TestCase):
    def setUp(self):
        self.default_data = {
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {"app": "my_app"},
        }

    def tearDown(self):
        REGISTRY.clear()

    def test_initialization(self):
        c = Counter(**self.default_data)
        self.assertEqual(self.default_data["name"], c.name)
        self.assertEqual(self.default_data["doc"], c.doc)
        self.assertEqual(self.default_data["const_labels"], c.const_labels)

        # check metrics automatically got registered
        collector_name = self.default_data["name"]
        self.assertIn(collector_name, REGISTRY.collectors)

    def test_set(self):
        c = Counter(**self.default_data)

        data = (
            {"labels": {"country": "sp", "device": "desktop"}, "values": range(10)},
            {"labels": {"country": "us", "device": "mobile"}, "values": range(10, 20)},
            {"labels": {"country": "uk", "device": "desktop"}, "values": range(20, 30)},
        )

        for i in data:
            for j in i["values"]:
                c.set(i["labels"], j)

        self.assertEqual(len(data), len(c.values))

    def test_get(self):
        c = Counter(**self.default_data)
        data = (
            {"labels": {"country": "sp", "device": "desktop"}, "values": range(10)},
            {"labels": {"country": "us", "device": "mobile"}, "values": range(10, 20)},
            {"labels": {"country": "uk", "device": "desktop"}, "values": range(20, 30)},
        )

        for i in data:
            for j in i["values"]:
                c.set(i["labels"], j)
                self.assertEqual(j, c.get(i["labels"]))

        # Last check
        for i in data:
            self.assertEqual(max(i["values"]), c.get(i["labels"]))

    def test_set_get_without_labels(self):
        c = Counter(**self.default_data)
        data = {"labels": {}, "values": range(100)}

        for i in data["values"]:
            c.set(data["labels"], i)

        self.assertEqual(1, len(c.values))

        self.assertEqual(max(data["values"]), c.get(data["labels"]))

    def test_inc(self):
        c = Counter(**self.default_data)
        iterations = 100
        labels = {"country": "sp", "device": "desktop"}

        for i in range(iterations):
            c.inc(labels)

        self.assertEqual(iterations, c.get(labels))

    def test_add(self):
        c = Counter(**self.default_data)
        labels = {"country": "sp", "device": "desktop"}
        iterations = 100

        for i in range(iterations):
            c.add(labels, i)

        self.assertEqual(sum(range(iterations)), c.get(labels))

    def test_negative_add(self):
        c = Counter(**self.default_data)
        labels = {"country": "sp", "device": "desktop"}

        with self.assertRaises(ValueError) as context:
            c.add(labels, -1)
        self.assertEqual("Counters can't decrease", str(context.exception))


class TestGaugeMetric(unittest.TestCase):
    def setUp(self):
        self.default_data = {
            "name": "hdd_disk_used",
            "doc": "Disk space used",
            "const_labels": {"server": "1.db.production.my-app"},
        }

    def tearDown(self):
        REGISTRY.clear()

    def test_initialization(self):
        g = Gauge(**self.default_data)
        self.assertEqual(self.default_data["name"], g.name)
        self.assertEqual(self.default_data["doc"], g.doc)
        self.assertEqual(self.default_data["const_labels"], g.const_labels)

        # check metrics automatically got registered
        collector_name = self.default_data["name"]
        self.assertIn(collector_name, REGISTRY.collectors)

    def test_set(self):
        g = Gauge(**self.default_data)
        data = (
            {"labels": {"max": "500G", "dev": "sda"}, "values": range(0, 500, 50)},
            {"labels": {"max": "1T", "dev": "sdb"}, "values": range(0, 1000, 100)},
            {"labels": {"max": "10T", "dev": "sdc"}, "values": range(0, 10000, 1000)},
        )

        for i in data:
            for j in i["values"]:
                g.set(i["labels"], j)

        self.assertEqual(len(data), len(g.values))

    def test_get(self):
        g = Gauge(**self.default_data)
        data = (
            {"labels": {"max": "500G", "dev": "sda"}, "values": range(0, 500, 50)},
            {"labels": {"max": "1T", "dev": "sdb"}, "values": range(0, 1000, 100)},
            {"labels": {"max": "10T", "dev": "sdc"}, "values": range(0, 10000, 1000)},
        )

        for i in data:
            for j in i["values"]:
                g.set(i["labels"], j)
                self.assertEqual(j, g.get(i["labels"]))

        for i in data:
            self.assertEqual(max(i["values"]), g.get(i["labels"]))

    def test_set_get_without_labels(self):
        g = Gauge(**self.default_data)
        data = {"labels": {}, "values": range(100)}

        for i in data["values"]:
            g.set(data["labels"], i)

        self.assertEqual(1, len(g.values))

        self.assertEqual(max(data["values"]), g.get(data["labels"]))

    def test_inc(self):
        g = Gauge(**self.default_data)
        iterations = 100
        labels = {"max": "10T", "dev": "sdc"}

        for i in range(iterations):
            g.inc(labels)
            self.assertEqual(i + 1, g.get(labels))

        self.assertEqual(iterations, g.get(labels))

    def test_dec(self):
        g = Gauge(**self.default_data)
        iterations = 100
        labels = {"max": "10T", "dev": "sdc"}
        g.set(labels, iterations)

        for i in range(iterations):
            g.dec(labels)
            self.assertEqual(iterations - (i + 1), g.get(labels))

        self.assertEqual(0, g.get(labels))

    def test_add(self):
        g = Gauge(**self.default_data)
        iterations = 100
        labels = {"max": "10T", "dev": "sdc"}

        for i in range(iterations):
            g.add(labels, i)

        self.assertEqual(sum(range(iterations)), g.get(labels))

    def test_add_negative(self):
        g = Gauge(**self.default_data)
        iterations = 100
        labels = {"max": "10T", "dev": "sdc"}

        for i in range(iterations):
            g.add(labels, -i)

        self.assertEqual(sum(map(lambda x: -x, range(iterations))), g.get(labels))

    def test_sub(self):
        g = Gauge(**self.default_data)
        iterations = 100
        labels = {"max": "10T", "dev": "sdc"}

        for i in range(iterations):
            g.sub(labels, i)

        self.assertEqual(sum(map(lambda x: -x, range(iterations))), g.get(labels))

    def test_sub_positive(self):
        g = Gauge(**self.default_data)
        iterations = 100
        labels = {"max": "10T", "dev": "sdc"}

        for i in range(iterations):
            g.sub(labels, -i)

        self.assertEqual(sum(range(iterations)), g.get(labels))


class TestSummaryMetric(unittest.TestCase):
    def setUp(self):
        self.default_data = {
            "name": "http_request_duration_microseconds",
            "doc": "Request duration per application",
            "const_labels": {"app": "my_app"},
        }

    def tearDown(self):
        REGISTRY.clear()

    def test_initialization(self):
        s = Summary(**self.default_data)
        self.assertEqual(self.default_data["name"], s.name)
        self.assertEqual(self.default_data["doc"], s.doc)
        self.assertEqual(self.default_data["const_labels"], s.const_labels)

        # check metrics automatically got registered
        collector_name = self.default_data["name"]
        self.assertIn(collector_name, REGISTRY.collectors)

    def test_add(self):
        s = Summary(**self.default_data)
        data = (
            {"labels": {"handler": "/static"}, "values": range(0, 500, 50)},
            {"labels": {"handler": "/p"}, "values": range(0, 1000, 100)},
            {"labels": {"handler": "/p/login"}, "values": range(0, 10000, 1000)},
        )

        for i in data:
            for j in i["values"]:
                s.add(i["labels"], j)

        for i in data:
            self.assertEqual(len(i["values"]), s.values[i["labels"]]._observations)

    def test_get(self):
        s = Summary(**self.default_data)
        labels = {"handler": "/static"}
        values = [3, 5.2, 13, 4]

        for i in values:
            s.add(labels, i)

        data = s.get(labels)
        correct_data = {"sum": 25.2, "count": 4, 0.50: 4.0, 0.90: 5.2, 0.99: 5.2}

        self.assertEqual(correct_data, data)

    def test_add_get_without_labels(self):
        s = Summary(**self.default_data)
        labels = None
        values = [3, 5.2, 13, 4]

        for i in values:
            s.add(labels, i)

        self.assertEqual(1, len(s.values))

        correct_data = {"sum": 25.2, "count": 4, 0.50: 4.0, 0.90: 5.2, 0.99: 5.2}
        self.assertEqual(correct_data, s.get(labels))

    def test_add_wrong_types(self):
        s = Summary(**self.default_data)
        labels = None
        values = ["3", (1, 2), {"1": 2}, True]

        for i in values:
            with self.assertRaises(TypeError) as context:
                s.add(labels, i)
        self.assertEqual(
            "Summary only works with digits (int, float)", str(context.exception)
        )


class TestHistogramMetric(unittest.TestCase):
    def setUp(self):
        self.default_data = {
            "name": "h",
            "doc": "doc",
            "const_labels": {"app": "my_app"},
            "buckets": [5.0, 10.0, 15.0],
        }

        self.expected_data = {
            "sum": 25.2,
            "count": 4,
            5.0: 2.0,
            10.0: 3.0,
            15.0: 4.0,
            POS_INF: 4.0,
        }
        self.input_values = [3, 5.2, 13, 4]

    def tearDown(self):
        REGISTRY.clear()

    def test_initialization(self):
        h = Histogram(**self.default_data)
        self.assertEqual(self.default_data["name"], h.name)
        self.assertEqual(self.default_data["doc"], h.doc)
        self.assertEqual(self.default_data["const_labels"], h.const_labels)

        # check metrics automatically got registered
        collector_name = self.default_data["name"]
        self.assertIn(collector_name, REGISTRY.collectors)

    def test_wrong_labels(self):
        h = Histogram(**self.default_data)
        with self.assertRaises(ValueError) as context:
            h.set_value({"le": 2}, 1)
        self.assertEqual("Invalid label name: le", str(context.exception))

    def test_insufficient_buckets(self):
        d = self.default_data.copy()
        d["buckets"] = []
        h = Histogram(**d)
        # The underlying histogram object within the Histogram metric is
        # created when needing so any exception only occurs when an new
        # observation is performed.
        with self.assertRaises(Exception) as context:
            h.observe(None, 3.0)
        self.assertEqual("Must have at least two buckets", str(context.exception))

    def test_unsorted_buckets(self):
        d = self.default_data.copy()
        d["buckets"] = [10.0, 5.0]
        h = Histogram(**d)
        # The underlying histogram object within the Histogram metric is
        # created when needing so any exception only occurs when an new
        # observation is performed.
        with self.assertRaises(Exception) as context:
            h.observe(None, 3.0)
        self.assertEqual("Buckets not in sorted order", str(context.exception))

    def test_expected_values(self):
        h = Histogram(**self.default_data)
        labels = None
        h.observe(labels, 7)
        results = h.get(labels)
        self.assertEqual(0, results[5.0])
        self.assertEqual(1, results[10.0])
        self.assertEqual(1, results[15.0])
        self.assertEqual(1, results[POS_INF])
        self.assertEqual(1, results["count"])
        self.assertEqual(7.0, results["sum"])

        h.observe(labels, 7.5)
        results = h.get(labels)
        self.assertEqual(0, results[5.0])
        self.assertEqual(2, results[10.0])
        self.assertEqual(2, results[15.0])
        self.assertEqual(2, results[POS_INF])
        self.assertEqual(2, results["count"])
        self.assertEqual(14.5, results["sum"])

        h.observe(labels, POS_INF)
        results = h.get(labels)
        self.assertEqual(0, results[5.0])
        self.assertEqual(2, results[10.0])
        self.assertEqual(2, results[15.0])
        self.assertEqual(3, results[POS_INF])
        self.assertEqual(3, results["count"])
        self.assertEqual(POS_INF, results["sum"])

    def test_get(self):
        h = Histogram(**self.default_data)
        labels = {"path": "/"}
        for i in self.input_values:
            h.observe(labels, i)
        data = h.get(labels)
        self.assertEqual(self.expected_data, data)

    def test_add_get_without_labels(self):
        h = Histogram(**self.default_data)
        labels = None
        for i in self.input_values:
            h.observe(labels, i)
        self.assertEqual(1, len(h.values))
        self.assertEqual(self.expected_data, h.get(labels))
