import datetime
import time
import unittest
import unittest.mock
import prometheus_metrics_proto as pmp
from aioprometheus.formats import BinaryFormatter, BINARY_CONTENT_TYPE
from aioprometheus import Collector, Counter, Gauge, Histogram, Summary, Registry


TEST_TIMESTAMP = 1515044377268


class TestProtobufFormat(unittest.TestCase):

    def setUp(self):

        self.const_labels = {"app": "my_app"}

        # Counter test fields
        self.counter_metric_name = "logged_users_total"
        self.counter_metric_help = "Logged users in the application."
        self.counter_metric_data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
        )

        # Gauge test fields
        self.gauge_metric_name = "logged_users_total"
        self.gauge_metric_help = "Logged users in the application."
        self.gauge_metric_data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
        )

        # Summary test fields
        self.summary_metric_name = "request_payload_size_bytes"
        self.summary_metric_help = "Request payload size in bytes."
        self.summary_metric_data = (
            ({"route": "/"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
        )
        self.summary_metric_data_values = (({"route": "/"}, (3, 5.2, 13, 4)),)

        # Histogram test fields
        self.histogram_metric_name = "request_latency_seconds"
        self.histogram_metric_help = "Request latency in seconds."
        self.histogram_metric_buckets = [5.0, 10.0, 15.0]
        # buckets typically have a POS_INF upper bound to catch values
        # beyond the largest bucket bound. Simulate this behavior.
        POS_INF = float("inf")
        self.histogram_metric_data = (
            (
                {"route": "/"},
                {5.0: 2, 10.0: 1, 15.0: 1, POS_INF: 0, "sum": 25.2, "count": 4},
            ),
        )
        self.histogram_metric_data_values = (({"route": "/"}, (3, 5.2, 13, 4)),)

    def test_headers_binary(self):
        """ check binary header info is provided """
        f = BinaryFormatter()
        expected_result = {"Content-Type": BINARY_CONTENT_TYPE}
        self.assertEqual(expected_result, f.get_headers())

    def test_no_metric_instances_present_binary(self):
        """ Check marshalling a collector with no metrics instances present """

        c = Counter(
            name=self.counter_metric_name,
            doc=self.counter_metric_help,
            const_labels=self.const_labels,
        )

        f = BinaryFormatter()

        result = f.marshall_collector(c)
        self.assertIsInstance(result, pmp.MetricFamily)

        # Construct the result expected to receive when the counter
        # collector is marshalled.
        expected_result = pmp.create_counter(
            self.counter_metric_name, self.counter_metric_help, []
        )

        self.assertEqual(result, expected_result)

    def test_counter_format_binary(self):

        # Check simple metric
        c = Counter(name=self.counter_metric_name, doc=self.counter_metric_help)

        # Add data to the collector
        for labels, value in self.counter_metric_data:
            c.set_value(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(c)
        self.assertIsInstance(result, pmp.MetricFamily)

        # Construct the result expected to receive when the counter
        # collector is marshalled.
        expected_result = pmp.create_counter(
            self.counter_metric_name, self.counter_metric_help, self.counter_metric_data
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with constant labels
        c = Counter(
            name=self.counter_metric_name,
            doc=self.counter_metric_help,
            const_labels=self.const_labels,
        )

        # Add data to the collector
        for labels, value in self.counter_metric_data:
            c.set_value(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(c)
        self.assertIsInstance(result, pmp.MetricFamily)

        # Construct the result to expected to receive when the counter
        # collector is marshalled.
        expected_result = pmp.create_counter(
            self.counter_metric_name,
            self.counter_metric_help,
            self.counter_metric_data,
            const_labels=self.const_labels,
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with timestamps
        with unittest.mock.patch.object(
            pmp.utils, "_timestamp_ms", return_value=TEST_TIMESTAMP
        ):

            c = Counter(name=self.counter_metric_name, doc=self.counter_metric_help)

            # Add data to the collector
            for labels, value in self.counter_metric_data:
                c.set_value(labels, value)

            f = BinaryFormatter(timestamp=True)

            result = f.marshall_collector(c)
            self.assertIsInstance(result, pmp.MetricFamily)

            # Construct the result to expected to receive when the counter
            # collector is marshalled.
            expected_result = pmp.create_counter(
                self.counter_metric_name,
                self.counter_metric_help,
                self.counter_metric_data,
                timestamp=True,
            )

            self.assertEqual(result, expected_result)

    def test_gauge_format_binary(self):

        g = Gauge(name=self.gauge_metric_name, doc=self.gauge_metric_help)

        # Add data to the collector
        for labels, values in self.gauge_metric_data:
            g.set_value(labels, values)

        f = BinaryFormatter()

        result = f.marshall_collector(g)
        self.assertIsInstance(result, pmp.MetricFamily)

        # Construct the result to expected to receive when the gauge
        # collector is marshalled.
        expected_result = pmp.create_gauge(
            self.gauge_metric_name, self.gauge_metric_help, self.gauge_metric_data
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with constant labels
        g = Gauge(
            name=self.gauge_metric_name,
            doc=self.gauge_metric_help,
            const_labels=self.const_labels,
        )

        # Add data to the collector
        for labels, values in self.gauge_metric_data:
            g.set_value(labels, values)

        f = BinaryFormatter()

        result = f.marshall_collector(g)
        self.assertIsInstance(result, pmp.MetricFamily)

        # Construct the result to expected to receive when the gauge
        # collector is marshalled.
        expected_result = pmp.create_gauge(
            self.gauge_metric_name,
            self.gauge_metric_help,
            self.gauge_metric_data,
            const_labels=self.const_labels,
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with timestamps
        with unittest.mock.patch.object(
            pmp.utils, "_timestamp_ms", return_value=TEST_TIMESTAMP
        ):

            g = Gauge(name=self.gauge_metric_name, doc=self.gauge_metric_help)

            # Add data to the collector
            for labels, values in self.gauge_metric_data:
                g.set_value(labels, values)

            f = BinaryFormatter(timestamp=True)

            result = f.marshall_collector(g)
            self.assertIsInstance(result, pmp.MetricFamily)

            # Construct the result to expected to receive when the gauge
            # collector is marshalled.
            expected_result = pmp.create_gauge(
                self.gauge_metric_name,
                self.gauge_metric_help,
                self.gauge_metric_data,
                timestamp=True,
            )

            self.assertEqual(result, expected_result)

    def test_summary_format_binary(self):

        s = Summary(name=self.summary_metric_name, doc=self.summary_metric_help)

        # Add data to the collector
        for labels, values in self.summary_metric_data_values:
            for value in values:
                s.add(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(s)
        self.assertIsInstance(result, pmp.MetricFamily)
        self.assertEqual(len(result.metric), 1)

        # Construct the result to expected to receive when the summary
        # collector is marshalled.
        expected_result = pmp.create_summary(
            self.summary_metric_name, self.summary_metric_help, self.summary_metric_data
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with constant labels
        s = Summary(
            name=self.summary_metric_name,
            doc=self.summary_metric_help,
            const_labels=self.const_labels,
        )

        # Add data to the collector
        for labels, values in self.summary_metric_data_values:
            for value in values:
                s.add(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(s)
        self.assertIsInstance(result, pmp.MetricFamily)
        self.assertEqual(len(result.metric), 1)

        # Construct the result to expected to receive when the summary
        # collector is marshalled.
        expected_result = pmp.create_summary(
            self.summary_metric_name,
            self.summary_metric_help,
            self.summary_metric_data,
            const_labels=self.const_labels,
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with timestamps
        with unittest.mock.patch.object(
            pmp.utils, "_timestamp_ms", return_value=TEST_TIMESTAMP
        ):

            s = Summary(name=self.summary_metric_name, doc=self.summary_metric_help)

            # Add data to the collector
            for labels, values in self.summary_metric_data_values:
                for value in values:
                    s.add(labels, value)

            f = BinaryFormatter(timestamp=True)

            result = f.marshall_collector(s)
            self.assertIsInstance(result, pmp.MetricFamily)
            self.assertEqual(len(result.metric), 1)

            # Construct the result to expected to receive when the summary
            # collector is marshalled.
            expected_result = pmp.create_summary(
                self.summary_metric_name,
                self.summary_metric_help,
                self.summary_metric_data,
                timestamp=True,
            )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with multiple metric instances

        input_summary_data = (
            ({"interval": "5s"}, [3, 5.2, 13, 4]),
            ({"interval": "10s"}, [1.3, 1.2, 32.1, 59.2, 109.46, 70.9]),
            ({"interval": "10s", "method": "fast"}, [5, 9.8, 31, 9.7, 101.4]),
        )

        managed_summary_data = (
            (
                {"interval": "5s"},
                {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4},
            ),
            (
                {"interval": "10s"},
                {
                    0.5: 32.1,
                    0.9: 59.2,
                    0.99: 59.2,
                    "sum": 274.15999999999997,
                    "count": 6,
                },
            ),
            (
                {"interval": "10s", "method": "fast"},
                {0.5: 9.7, 0.9: 9.8, 0.99: 9.8, "sum": 156.9, "count": 5},
            ),
        )

        s = Summary(name=self.summary_metric_name, doc=self.summary_metric_help)

        # Add data to the collector
        for labels, values in input_summary_data:
            for value in values:
                s.add(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(s)
        self.assertIsInstance(result, pmp.MetricFamily)
        self.assertEqual(len(result.metric), 3)

        # Construct the result to expected to receive when the summary
        # collector is marshalled.
        expected_result = pmp.create_summary(
            self.summary_metric_name, self.summary_metric_help, managed_summary_data
        )

        self.assertEqual(result, expected_result)

    def test_histogram_format_binary(self):

        h = Histogram(
            name=self.histogram_metric_name,
            doc=self.histogram_metric_help,
            buckets=self.histogram_metric_buckets,
        )

        # Add data to the collector
        for labels, values in self.histogram_metric_data_values:
            for value in values:
                h.add(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(h)
        self.assertIsInstance(result, pmp.MetricFamily)
        self.assertEqual(len(result.metric), 1)

        # Construct the result to expected to receive when the histogram
        # collector is marshalled.
        expected_result = pmp.create_histogram(
            self.histogram_metric_name,
            self.histogram_metric_help,
            self.histogram_metric_data,
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with constant labels
        h = Histogram(
            name=self.histogram_metric_name,
            doc=self.histogram_metric_help,
            const_labels=self.const_labels,
            buckets=self.histogram_metric_buckets,
        )

        # Add data to the collector
        for labels, values in self.histogram_metric_data_values:
            for value in values:
                h.add(labels, value)

        f = BinaryFormatter()

        result = f.marshall_collector(h)
        self.assertIsInstance(result, pmp.MetricFamily)
        self.assertEqual(len(result.metric), 1)

        # Construct the result to expected to receive when the histogram
        # collector is marshalled.
        expected_result = pmp.create_histogram(
            self.histogram_metric_name,
            self.histogram_metric_help,
            self.histogram_metric_data,
            const_labels=self.const_labels,
        )

        self.assertEqual(result, expected_result)

        ######################################################################

        # Check metric with timestamps
        with unittest.mock.patch.object(
            pmp.utils, "_timestamp_ms", return_value=TEST_TIMESTAMP
        ):

            h = Histogram(
                name=self.histogram_metric_name,
                doc=self.histogram_metric_help,
                buckets=self.histogram_metric_buckets,
            )

            # Add data to the collector
            for labels, values in self.histogram_metric_data_values:
                for value in values:
                    h.add(labels, value)

            f = BinaryFormatter(timestamp=True)

            result = f.marshall_collector(h)
            self.assertIsInstance(result, pmp.MetricFamily)
            self.assertEqual(len(result.metric), 1)

            # Construct the result to expected to receive when the histogram
            # collector is marshalled.
            expected_result = pmp.create_histogram(
                self.histogram_metric_name,
                self.histogram_metric_help,
                self.histogram_metric_data,
                timestamp=True,
            )

        self.assertEqual(result, expected_result)

    def test_registry_marshall_counter(self):

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        counter = Counter(
            "counter_test", "A counter.", const_labels={"type": "counter"}
        )

        for labels, value in counter_data:
            counter.set(labels, value)

        registry = Registry()
        registry.register(counter)

        valid_result = (
            b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n\r'
            b"\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample\x12"
            b"\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t\x00\x00"
            b"\x00\x00\x00\x00y@"
        )
        f = BinaryFormatter()

        self.assertEqual(valid_result, f.marshall(registry))

    def test_registry_marshall_gauge(self):

        gauge_data = (({"g_sample": "1", "g_subsample": "b"}, 800),)

        gauge = Gauge("gauge_test", "A gauge.", const_labels={"type": "gauge"})

        for labels, value in gauge_data:
            gauge.set(labels, value)

        registry = Registry()
        registry.register(gauge)

        valid_result = (
            b'U\n\ngauge_test\x12\x08A gauge.\x18\x01";'
            b"\n\r\n\x08g_sample\x12\x011\n\x10\n\x0bg_subsample"
            b"\x12\x01b\n\r\n\x04type\x12\x05gauge\x12\t\t\x00"
            b"\x00\x00\x00\x00\x00\x89@"
        )

        f = BinaryFormatter()

        self.assertEqual(valid_result, f.marshall(registry))

    def test_registry_marshall_summary(self):

        metric_name = "summary_test"
        metric_help = "A summary."
        # metric_data = (
        #     ({'s_sample': '1', 's_subsample': 'b'},
        #      {0.5: 4235.0, 0.9: 4470.0, 0.99: 4517.0, 'count': 22, 'sum': 98857.0}),
        # )

        summary_data = (({"s_sample": "1", "s_subsample": "b"}, range(4000, 5000, 47)),)

        summary = Summary(metric_name, metric_help, const_labels={"type": "summary"})

        for labels, values in summary_data:
            for v in values:
                summary.add(labels, v)

        registry = Registry()
        registry.register(summary)

        valid_result = (
            b"\x99\x01\n\x0csummary_test\x12\nA summary."
            b'\x18\x02"{\n\r\n\x08s_sample\x12\x011\n\x10\n'
            b"\x0bs_subsample\x12\x01b\n\x0f\n\x04type\x12\x07"
            b'summary"G\x08\x16\x11\x00\x00\x00\x00\x90"\xf8@'
            b"\x1a\x12\t\x00\x00\x00\x00\x00\x00\xe0?\x11\x00"
            b"\x00\x00\x00\x00\x8b\xb0@\x1a\x12\t\xcd\xcc\xcc"
            b"\xcc\xcc\xcc\xec?\x11\x00\x00\x00\x00\x00v\xb1@"
            b"\x1a\x12\t\xaeG\xe1z\x14\xae\xef?\x11\x00\x00\x00"
            b"\x00\x00\xa5\xb1@"
        )

        f = BinaryFormatter()

        self.assertEqual(valid_result, f.marshall(registry))

    def test_registry_marshall_histogram(self):
        """ check encode of histogram matches expected output """

        metric_name = "histogram_test"
        metric_help = "A histogram."
        metric_data = (
            (
                {"h_sample": "1", "h_subsample": "b"},
                {5.0: 3, 10.0: 2, 15.0: 1, "count": 6, "sum": 46.0},
            ),
        )
        histogram_data = (
            ({"h_sample": "1", "h_subsample": "b"}, (4.5, 5.0, 4.0, 9.6, 9.0, 13.9)),
        )

        POS_INF = float("inf")
        histogram = Histogram(
            metric_name,
            metric_help,
            const_labels={"type": "histogram"},
            buckets=(5.0, 10.0, 15.0, POS_INF),
        )
        for labels, values in histogram_data:
            for v in values:
                histogram.add(labels, v)

        registry = Registry()
        registry.register(histogram)

        valid_result = (
            b"\x97\x01\n\x0ehistogram_test\x12\x0cA histogram."
            b'\x18\x04"u\n\r\n\x08h_sample\x12\x011\n\x10\n'
            b"\x0bh_subsample\x12\x01b\n\x11\n\x04type\x12\t"
            b"histogram:?\x08\x06\x11\x00\x00\x00\x00\x00\x00G@"
            b"\x1a\x0b\x08\x03\x11\x00\x00\x00\x00\x00\x00\x14@"
            b"\x1a\x0b\x08\x02\x11\x00\x00\x00\x00\x00\x00$@\x1a"
            b"\x0b\x08\x01\x11\x00\x00\x00\x00\x00\x00.@\x1a\x0b"
            b"\x08\x00\x11\x00\x00\x00\x00\x00\x00\xf0\x7f"
        )

        f = BinaryFormatter()

        self.assertEqual(valid_result, f.marshall(registry))
