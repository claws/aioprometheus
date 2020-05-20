import asynctest
import aiohttp
import unittest.mock
from aiohttp.hdrs import ACCEPT, CONTENT_TYPE
import aioprometheus
import prometheus_metrics_proto as pmp

from aioprometheus import Counter, Gauge, Histogram, Registry, Service, Summary
from aioprometheus.formats import text, binary


TEXT = "text"
BINARY = "binary"
format_kinds = {TEXT: text.TEXT_CONTENT_TYPE, BINARY: binary.BINARY_CONTENT_TYPE}


class TestTextExporter(asynctest.TestCase):
    async def setUp(self):
        self.registry = Registry()
        self.server = Service(registry=self.registry)
        await self.server.start(addr="127.0.0.1")
        self.metrics_url = self.server.metrics_url
        self.root_url = self.server.root_url

    async def tearDown(self):
        await self.server.stop()

    async def test_invalid_registry(self):
        """ check only valid registry can be provided """
        for invalid_registry in ["nope", dict(), list()]:
            with self.assertRaises(Exception) as cm:
                Service(registry=invalid_registry)
            self.assertIn("registry must be a Registry, got:", str(cm.exception))

        Service(registry=Registry())

    def test_fetch_url_before_starting_server(self):
        """ check accessing a URL property raises expection if not available """
        s = Service()

        with self.assertRaises(Exception) as cm:
            _ = s.root_url
        self.assertIn(
            "No URL available, Prometheus metrics server is not running",
            str(cm.exception),
        )

        with self.assertRaises(Exception) as cm:
            _ = s.metrics_url
        self.assertIn(
            "No URL available, Prometheus metrics server is not running",
            str(cm.exception),
        )

    def test_register_deregister(self):
        """ check registering and deregistering metrics """
        c = Counter("test_counter", "Test Counter.", {"test": "test_counter"})
        self.server.register(c)

        # Check registering a collector with same name raises an exception
        c2 = Counter("test_counter", "Another Test Counter.")
        with self.assertRaises(ValueError) as cm:
            self.server.register(c2)
        self.assertIn("is already registered", str(cm.exception))

        self.server.deregister("test_counter")

        # Check deregistering a non-existant collector raises an exception
        with self.assertRaises(KeyError) as cm:
            self.server.deregister("test_counter")

    async def test_start_started_server(self):
        """ check starting a started server """

        with unittest.mock.patch.object(
            aioprometheus.service.logger, "warning"
        ) as mock_warn:
            await self.server.start(addr="127.0.0.1")
            self.assertEqual(mock_warn.call_count, 1)
            mock_warn.assert_called_once_with(
                "Prometheus metrics server is already running"
            )

    async def test_stop_stopped_server(self):
        """ check stopping a stopped server """

        s = Service(registry=self.registry)
        await s.start(addr="127.0.0.1")
        await s.stop()

        with unittest.mock.patch.object(
            aioprometheus.service.logger, "warning"
        ) as mock_warn:
            await s.stop()
            self.assertEqual(mock_warn.call_count, 1)
            mock_warn.assert_called_once_with(
                "Prometheus metrics server is already stopped"
            )

    async def test_counter(self):
        """ check counter metric export """

        # Add some metrics
        data = (
            ({"data": 1}, 100),
            ({"data": "2"}, 200),
            ({"data": 3}, 300),
            ({"data": 1}, 400),
        )
        c = Counter("test_counter", "Test Counter.", {"test": "test_counter"})
        self.server.register(c)

        for i in data:
            c.set(i[0], i[1])

        expected_data = """# HELP test_counter Test Counter.
# TYPE test_counter counter
test_counter{data="1",test="test_counter"} 400
test_counter{data="2",test="test_counter"} 200
test_counter{data="3",test="test_counter"} 300
"""

        async with aiohttp.ClientSession() as session:

            # Fetch as text
            async with session.get(
                self.metrics_url, headers={ACCEPT: text.TEXT_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(text.TEXT_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE))
                self.assertEqual(expected_data, content.decode())

            # Fetch as binary
            async with session.get(
                self.metrics_url, headers={ACCEPT: binary.BINARY_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(
                    binary.BINARY_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE)
                )
                metrics = pmp.decode(content)
                self.assertEqual(len(metrics), 1)
                mf = metrics[0]
                self.assertIsInstance(mf, pmp.MetricFamily)
                self.assertEqual(mf.type, pmp.COUNTER)
                self.assertEqual(len(mf.metric), 3)

    async def test_gauge(self):
        """ check gauge metric export """

        # Add some metrics
        data = (
            ({"data": 1}, 100),
            ({"data": "2"}, 200),
            ({"data": 3}, 300),
            ({"data": 1}, 400),
        )
        g = Gauge("test_gauge", "Test Gauge.", {"test": "test_gauge"})
        self.server.register(g)

        for i in data:
            g.set(i[0], i[1])

        expected_data = """# HELP test_gauge Test Gauge.
# TYPE test_gauge gauge
test_gauge{data="1",test="test_gauge"} 400
test_gauge{data="2",test="test_gauge"} 200
test_gauge{data="3",test="test_gauge"} 300
"""

        async with aiohttp.ClientSession() as session:

            # Fetch as text
            async with session.get(
                self.metrics_url, headers={ACCEPT: text.TEXT_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(text.TEXT_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE))
                self.assertEqual(expected_data, content.decode())

            # Fetch as binary
            async with session.get(
                self.metrics_url, headers={ACCEPT: binary.BINARY_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(
                    binary.BINARY_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE)
                )
                metrics = pmp.decode(content)
                self.assertEqual(len(metrics), 1)
                mf = metrics[0]
                self.assertIsInstance(mf, pmp.MetricFamily)
                self.assertEqual(mf.type, pmp.GAUGE)
                self.assertEqual(len(mf.metric), 3)

    async def test_summary(self):
        """ check summary metric export """

        # Add some metrics
        data = [3, 5.2, 13, 4]
        label = {"data": 1}

        s = Summary("test_summary", "Test Summary.", {"test": "test_summary"})
        self.server.register(s)

        for i in data:
            s.add(label, i)

        expected_data = """# HELP test_summary Test Summary.
# TYPE test_summary summary
test_summary{data="1",quantile="0.5",test="test_summary"} 4.0
test_summary{data="1",quantile="0.9",test="test_summary"} 5.2
test_summary{data="1",quantile="0.99",test="test_summary"} 5.2
test_summary_count{data="1",test="test_summary"} 4
test_summary_sum{data="1",test="test_summary"} 25.2
"""

        async with aiohttp.ClientSession() as session:

            # Fetch as text
            async with session.get(
                self.metrics_url, headers={ACCEPT: text.TEXT_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(text.TEXT_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE))
                self.assertEqual(expected_data, content.decode())

            # Fetch as binary
            async with session.get(
                self.metrics_url, headers={ACCEPT: binary.BINARY_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(
                    binary.BINARY_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE)
                )
                metrics = pmp.decode(content)
                self.assertEqual(len(metrics), 1)
                mf = metrics[0]
                self.assertIsInstance(mf, pmp.MetricFamily)
                self.assertEqual(mf.type, pmp.SUMMARY)
                self.assertEqual(len(mf.metric), 1)
                self.assertEqual(len(mf.metric[0].summary.quantile), 3)

    async def test_histogram(self):
        """ check histogram metric export """

        # Add some metrics
        data = [3, 5.2, 13, 4]
        label = {"data": 1}

        h = Histogram(
            "histogram_test",
            "Test Histogram.",
            {"type": "test_histogram"},
            buckets=[5.0, 10.0, 15.0],
        )
        self.server.register(h)

        for i in data:
            h.add(label, i)

        expected_data = """# HELP histogram_test Test Histogram.
# TYPE histogram_test histogram
histogram_test_bucket{data="1",le="5.0",type="test_histogram"} 2.0
histogram_test_bucket{data="1",le="10.0",type="test_histogram"} 3.0
histogram_test_bucket{data="1",le="15.0",type="test_histogram"} 4.0
histogram_test_bucket{data="1",le="+Inf",type="test_histogram"} 4.0
histogram_test_count{data="1",type="test_histogram"} 4.0
histogram_test_sum{data="1",type="test_histogram"} 25.2
"""

        async with aiohttp.ClientSession() as session:

            # Fetch as text
            async with session.get(
                self.metrics_url, headers={ACCEPT: text.TEXT_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(text.TEXT_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE))
                self.assertEqual(expected_data, content.decode())

            # Fetch as binary
            async with session.get(
                self.metrics_url, headers={ACCEPT: binary.BINARY_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(
                    binary.BINARY_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE)
                )
                metrics = pmp.decode(content)
                self.assertEqual(len(metrics), 1)
                mf = metrics[0]
                self.assertIsInstance(mf, pmp.MetricFamily)
                self.assertEqual(mf.type, pmp.HISTOGRAM)
                self.assertEqual(len(mf.metric), 1)
                self.assertEqual(len(mf.metric[0].histogram.bucket), 4)

    async def test_all(self):

        counter_data = (
            ({"c_sample": "1"}, 100),
            ({"c_sample": "2"}, 200),
            ({"c_sample": "3"}, 300),
            ({"c_sample": "1", "c_subsample": "b"}, 400),
        )

        gauge_data = (
            ({"g_sample": "1"}, 500),
            ({"g_sample": "2"}, 600),
            ({"g_sample": "3"}, 700),
            ({"g_sample": "1", "g_subsample": "b"}, 800),
        )

        summary_data = (
            ({"s_sample": "1"}, range(1000, 2000, 4)),
            ({"s_sample": "2"}, range(2000, 3000, 20)),
            ({"s_sample": "3"}, range(3000, 4000, 13)),
            ({"s_sample": "1", "s_subsample": "b"}, range(4000, 5000, 47)),
        )

        histogram_data = (
            ({"h_sample": "1"}, [3, 14]),
            ({"h_sample": "2"}, range(1, 20, 2)),
            ({"h_sample": "3"}, range(1, 20, 2)),
            ({"h_sample": "1", "h_subsample": "b"}, range(1, 20, 2)),
        )

        counter = Counter("counter_test", "A counter.", {"type": "counter"})
        gauge = Gauge("gauge_test", "A gauge.", {"type": "gauge"})
        summary = Summary("summary_test", "A summary.", {"type": "summary"})
        histogram = Histogram(
            "histogram_test",
            "A histogram.",
            {"type": "histogram"},
            buckets=[5.0, 10.0, 15.0],
        )

        self.server.register(counter)
        self.server.register(gauge)
        self.server.register(summary)
        self.server.register(histogram)

        # Add data
        [counter.set(c[0], c[1]) for c in counter_data]
        [gauge.set(g[0], g[1]) for g in gauge_data]
        [summary.add(i[0], s) for i in summary_data for s in i[1]]
        [histogram.observe(i[0], h) for i in histogram_data for h in i[1]]

        expected_data = """# HELP counter_test A counter.
# TYPE counter_test counter
counter_test{c_sample="1",type="counter"} 100
counter_test{c_sample="2",type="counter"} 200
counter_test{c_sample="3",type="counter"} 300
counter_test{c_sample="1",c_subsample="b",type="counter"} 400
# HELP gauge_test A gauge.
# TYPE gauge_test gauge
gauge_test{g_sample="1",type="gauge"} 500
gauge_test{g_sample="2",type="gauge"} 600
gauge_test{g_sample="3",type="gauge"} 700
gauge_test{g_sample="1",g_subsample="b",type="gauge"} 800
# HELP histogram_test A histogram.
# TYPE histogram_test histogram
histogram_test_bucket{h_sample="1",le="5.0",type="histogram"} 1.0
histogram_test_bucket{h_sample="1",le="10.0",type="histogram"} 1.0
histogram_test_bucket{h_sample="1",le="15.0",type="histogram"} 2.0
histogram_test_bucket{h_sample="1",le="+Inf",type="histogram"} 2.0
histogram_test_count{h_sample="1",type="histogram"} 2.0
histogram_test_sum{h_sample="1",type="histogram"} 17.0
histogram_test_bucket{h_sample="2",le="5.0",type="histogram"} 3.0
histogram_test_bucket{h_sample="2",le="10.0",type="histogram"} 5.0
histogram_test_bucket{h_sample="2",le="15.0",type="histogram"} 8.0
histogram_test_bucket{h_sample="2",le="+Inf",type="histogram"} 10.0
histogram_test_count{h_sample="2",type="histogram"} 10.0
histogram_test_sum{h_sample="2",type="histogram"} 100.0
histogram_test_bucket{h_sample="3",le="5.0",type="histogram"} 3.0
histogram_test_bucket{h_sample="3",le="10.0",type="histogram"} 5.0
histogram_test_bucket{h_sample="3",le="15.0",type="histogram"} 8.0
histogram_test_bucket{h_sample="3",le="+Inf",type="histogram"} 10.0
histogram_test_count{h_sample="3",type="histogram"} 10.0
histogram_test_sum{h_sample="3",type="histogram"} 100.0
histogram_test_bucket{h_sample="1",h_subsample="b",le="5.0",type="histogram"} 3.0
histogram_test_bucket{h_sample="1",h_subsample="b",le="10.0",type="histogram"} 5.0
histogram_test_bucket{h_sample="1",h_subsample="b",le="15.0",type="histogram"} 8.0
histogram_test_bucket{h_sample="1",h_subsample="b",le="+Inf",type="histogram"} 10.0
histogram_test_count{h_sample="1",h_subsample="b",type="histogram"} 10.0
histogram_test_sum{h_sample="1",h_subsample="b",type="histogram"} 100.0
# HELP summary_test A summary.
# TYPE summary_test summary
summary_test{quantile="0.5",s_sample="1",type="summary"} 1272.0
summary_test{quantile="0.9",s_sample="1",type="summary"} 1452.0
summary_test{quantile="0.99",s_sample="1",type="summary"} 1496.0
summary_test_count{s_sample="1",type="summary"} 250
summary_test_sum{s_sample="1",type="summary"} 374500.0
summary_test{quantile="0.5",s_sample="2",type="summary"} 2260.0
summary_test{quantile="0.9",s_sample="2",type="summary"} 2440.0
summary_test{quantile="0.99",s_sample="2",type="summary"} 2500.0
summary_test_count{s_sample="2",type="summary"} 50
summary_test_sum{s_sample="2",type="summary"} 124500.0
summary_test{quantile="0.5",s_sample="3",type="summary"} 3260.0
summary_test{quantile="0.9",s_sample="3",type="summary"} 3442.0
summary_test{quantile="0.99",s_sample="3",type="summary"} 3494.0
summary_test_count{s_sample="3",type="summary"} 77
summary_test_sum{s_sample="3",type="summary"} 269038.0
summary_test{quantile="0.5",s_sample="1",s_subsample="b",type="summary"} 4235.0
summary_test{quantile="0.9",s_sample="1",s_subsample="b",type="summary"} 4470.0
summary_test{quantile="0.99",s_sample="1",s_subsample="b",type="summary"} 4517.0
summary_test_count{s_sample="1",s_subsample="b",type="summary"} 22
summary_test_sum{s_sample="1",s_subsample="b",type="summary"} 98857.0
"""

        async with aiohttp.ClientSession() as session:

            # Fetch as text
            async with session.get(
                self.metrics_url, headers={ACCEPT: text.TEXT_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(text.TEXT_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE))
                self.assertEqual(expected_data, content.decode())

            # Fetch as binary
            async with session.get(
                self.metrics_url, headers={ACCEPT: binary.BINARY_CONTENT_TYPE}
            ) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(
                    binary.BINARY_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE)
                )
                metrics = pmp.decode(content)
                self.assertEqual(len(metrics), 4)
                for mf in metrics:
                    self.assertIsInstance(mf, pmp.MetricFamily)
                    if mf.type == pmp.COUNTER:
                        self.assertEqual(len(mf.metric), 4)
                    elif mf.type == pmp.GAUGE:
                        self.assertEqual(len(mf.metric), 4)
                    elif mf.type == pmp.SUMMARY:
                        self.assertEqual(len(mf.metric), 4)
                        self.assertEqual(len(mf.metric[0].summary.quantile), 3)
                    elif mf.type == pmp.HISTOGRAM:
                        self.assertEqual(len(mf.metric), 4)
                        self.assertEqual(len(mf.metric[0].histogram.bucket), 4)

    async def test_no_accept_header(self):
        """ check default format is used when no accept header is defined """

        # Add some metrics
        data = (({"data": 1}, 100),)
        c = Counter("test_counter", "Test Counter.", {"test": "test_counter"})
        self.server.register(c)

        for i in data:
            c.set(i[0], i[1])

        expected_data = """# HELP test_counter Test Counter.
# TYPE test_counter counter
test_counter{data="1",test="test_counter"} 100
"""

        async with aiohttp.ClientSession() as session:

            # Fetch without explicit accept type
            async with session.get(self.metrics_url) as resp:
                self.assertEqual(resp.status, 200)
                content = await resp.read()
                self.assertEqual(text.TEXT_CONTENT_TYPE, resp.headers.get(CONTENT_TYPE))
                self.assertEqual(expected_data, content.decode())

            # TODO: Add another test here that includes the ACCEPT header
            # but with no value set. I have not worked out how to do this
            # yet as aiohttp expects headers to be a dict and a value of None
            # is not permitted.

    async def test_root_route(self):
        """ check root route returns content """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.root_url) as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("text/html", resp.headers.get(CONTENT_TYPE))

    async def test_robots_route(self):
        """ check robots route returns content """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.root_url}robots.txt") as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("text/plain", resp.headers.get(CONTENT_TYPE))
