
import aiohttp

from aiohttp.hdrs import ACCEPT, CONTENT_TYPE

from aioprometheus import (
    Counter,
    Gauge,
    Histogram,
    Registry,
    Service,
    Summary)
from aioprometheus.test_utils import AsyncioTestCase

TEST_PORT = 61423
TEST_HOST = "127.0.0.1"


class TestTextExporter(AsyncioTestCase):

    async def setUp(self):
        self.registry = Registry()
        self.server = Service(registry=self.registry, loop=self.loop)
        await self.server.start(addr=TEST_HOST, port=TEST_PORT)
        self.metrics_url = self.server.url

    async def tearDown(self):
        await self.server.stop()

    async def test_invalid_registry(self):
        ''' check only valid registry can be provided '''
        for invalid_registry in ['nope', dict(), list()]:
            with self.assertRaises(Exception) as cm:
                Service(registry=invalid_registry, loop=self.loop)
            self.assertIn(
                'registry must be a Registry, got:', str(cm.exception))

        Service(registry=Registry(), loop=self.loop)

    async def test_counter(self):

        # Add some metrics
        data = (
            ({'data': 1}, 100),
            ({'data': "2"}, 200),
            ({'data': 3}, 300),
            ({'data': 1}, 400),
        )
        c = Counter("test_counter", "Test Counter.", {'test': "test_counter"})
        self.registry.register(c)

        for i in data:
            c.set(i[0], i[1])

        expected_data = """# HELP test_counter Test Counter.
# TYPE test_counter counter
test_counter{data="1",test="test_counter"} 400
test_counter{data="2",test="test_counter"} 200
test_counter{data="3",test="test_counter"} 300
"""

        with aiohttp.ClientSession(loop=self.loop) as session:
            headers = {ACCEPT: 'text/plain; version=0.0.4'}
            async with session.get(self.metrics_url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                self.assertEqual("text/plain; version=0.0.4; charset=utf-8",
                                 resp.headers.get(CONTENT_TYPE))
                self.assertEqual(200, resp.status)
                self.assertEqual(expected_data, content.decode())

    async def test_gauge(self):

        # Add some metrics
        data = (
            ({'data': 1}, 100),
            ({'data': "2"}, 200),
            ({'data': 3}, 300),
            ({'data': 1}, 400),
        )
        g = Gauge("test_gauge", "Test Gauge.", {'test': "test_gauge"})
        self.registry.register(g)

        for i in data:
            g.set(i[0], i[1])

        expected_data = """# HELP test_gauge Test Gauge.
# TYPE test_gauge gauge
test_gauge{data="1",test="test_gauge"} 400
test_gauge{data="2",test="test_gauge"} 200
test_gauge{data="3",test="test_gauge"} 300
"""

        with aiohttp.ClientSession(loop=self.loop) as session:
            headers = {ACCEPT: 'text/plain; version=0.0.4'}
            async with session.get(self.metrics_url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                self.assertEqual("text/plain; version=0.0.4; charset=utf-8",
                                 resp.headers.get(CONTENT_TYPE))
                self.assertEqual(200, resp.status)
                self.assertEqual(expected_data, content.decode())

    async def test_summary(self):

        # Add some metrics
        data = [3, 5.2, 13, 4]
        label = {'data': 1}

        s = Summary("test_summary", "Test Summary.", {'test': "test_summary"})
        self.registry.register(s)

        for i in data:
            s.add(label, i)

        expected_data = """# HELP test_summary Test Summary.
# TYPE test_summary summary
test_summary_count{data="1",test="test_summary"} 4
test_summary_sum{data="1",test="test_summary"} 25.2
test_summary{data="1",quantile="0.5",test="test_summary"} 4.0
test_summary{data="1",quantile="0.9",test="test_summary"} 5.2
test_summary{data="1",quantile="0.99",test="test_summary"} 5.2
"""

        with aiohttp.ClientSession(loop=self.loop) as session:
            headers = {ACCEPT: 'text/plain; version=0.0.4'}
            async with session.get(self.metrics_url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                self.assertEqual("text/plain; version=0.0.4; charset=utf-8",
                                 resp.headers.get(CONTENT_TYPE))
                self.assertEqual(200, resp.status)
                self.assertEqual(expected_data, content.decode())

    async def test_histogram(self):
        pass

        # Add some metrics
        data = [3, 5.2, 13, 4]
        label = {'data': 1}

        h = Histogram(
            "histogram_test", "Test Histogram.", {'type': "test_histogram"},
            buckets=[5.0, 10.0, 15.0])
        self.registry.register(h)

        for i in data:
            h.add(label, i)

        expected_data = """# HELP histogram_test Test Histogram.
# TYPE histogram_test histogram
histogram_test_bucket{data="1",le="+Inf",type="test_histogram"} 0
histogram_test_bucket{data="1",le="10.0",type="test_histogram"} 1
histogram_test_bucket{data="1",le="15.0",type="test_histogram"} 1
histogram_test_bucket{data="1",le="5.0",type="test_histogram"} 2
histogram_test_count{data="1",type="test_histogram"} 4
histogram_test_sum{data="1",type="test_histogram"} 25.2
"""

        with aiohttp.ClientSession(loop=self.loop) as session:
            headers = {ACCEPT: 'text/plain; version=0.0.4'}
            async with session.get(self.metrics_url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                self.assertEqual("text/plain; version=0.0.4; charset=utf-8",
                                 resp.headers.get(CONTENT_TYPE))
                self.assertEqual(200, resp.status)
                self.assertEqual(expected_data, content.decode())

    async def test_all(self):

        counter_data = (
            ({'c_sample': '1'}, 100),
            ({'c_sample': '2'}, 200),
            ({'c_sample': '3'}, 300),
            ({'c_sample': '1', 'c_subsample': 'b'}, 400),
        )

        gauge_data = (
            ({'g_sample': '1'}, 500),
            ({'g_sample': '2'}, 600),
            ({'g_sample': '3'}, 700),
            ({'g_sample': '1', 'g_subsample': 'b'}, 800),
        )

        summary_data = (
            ({'s_sample': '1'}, range(1000, 2000, 4)),
            ({'s_sample': '2'}, range(2000, 3000, 20)),
            ({'s_sample': '3'}, range(3000, 4000, 13)),
            ({'s_sample': '1', 's_subsample': 'b'}, range(4000, 5000, 47)),
        )

        histogram_data = (
            ({'h_sample': '1'}, range(1, 20, 2)),
            ({'h_sample': '2'}, range(1, 20, 2)),
            ({'h_sample': '3'}, range(1, 20, 2)),
            ({'h_sample': '1', 'h_subsample': 'b'}, range(1, 20, 2)),
        )

        counter = Counter("counter_test", "A counter.", {'type': "counter"})
        gauge = Gauge("gauge_test", "A gauge.", {'type': "gauge"})
        summary = Summary("summary_test", "A summary.", {'type': "summary"})
        histogram = Histogram(
            "histogram_test", "A histogram.", {'type': "histogram"},
            buckets=[5.0, 10.0, 15.0])

        self.registry.register(counter)
        self.registry.register(gauge)
        self.registry.register(summary)
        self.registry.register(histogram)

        # Add data
        [counter.set(c[0], c[1]) for c in counter_data]
        [gauge.set(g[0], g[1]) for g in gauge_data]
        [summary.add(i[0], s) for i in summary_data for s in i[1]]
        [histogram.add(i[0], h) for i in histogram_data for h in i[1]]

        expected_data = """# HELP counter_test A counter.
# TYPE counter_test counter
counter_test{c_sample="1",c_subsample="b",type="counter"} 400
counter_test{c_sample="1",type="counter"} 100
counter_test{c_sample="2",type="counter"} 200
counter_test{c_sample="3",type="counter"} 300
# HELP gauge_test A gauge.
# TYPE gauge_test gauge
gauge_test{g_sample="1",g_subsample="b",type="gauge"} 800
gauge_test{g_sample="1",type="gauge"} 500
gauge_test{g_sample="2",type="gauge"} 600
gauge_test{g_sample="3",type="gauge"} 700
# HELP histogram_test A histogram.
# TYPE histogram_test histogram
histogram_test_bucket{h_sample="1",h_subsample="b",le="+Inf",type="histogram"} 2
histogram_test_bucket{h_sample="1",h_subsample="b",le="10.0",type="histogram"} 2
histogram_test_bucket{h_sample="1",h_subsample="b",le="15.0",type="histogram"} 3
histogram_test_bucket{h_sample="1",h_subsample="b",le="5.0",type="histogram"} 3
histogram_test_bucket{h_sample="1",le="+Inf",type="histogram"} 2
histogram_test_bucket{h_sample="1",le="10.0",type="histogram"} 2
histogram_test_bucket{h_sample="1",le="15.0",type="histogram"} 3
histogram_test_bucket{h_sample="1",le="5.0",type="histogram"} 3
histogram_test_bucket{h_sample="2",le="+Inf",type="histogram"} 2
histogram_test_bucket{h_sample="2",le="10.0",type="histogram"} 2
histogram_test_bucket{h_sample="2",le="15.0",type="histogram"} 3
histogram_test_bucket{h_sample="2",le="5.0",type="histogram"} 3
histogram_test_bucket{h_sample="3",le="+Inf",type="histogram"} 2
histogram_test_bucket{h_sample="3",le="10.0",type="histogram"} 2
histogram_test_bucket{h_sample="3",le="15.0",type="histogram"} 3
histogram_test_bucket{h_sample="3",le="5.0",type="histogram"} 3
histogram_test_count{h_sample="1",h_subsample="b",type="histogram"} 10
histogram_test_count{h_sample="1",type="histogram"} 10
histogram_test_count{h_sample="2",type="histogram"} 10
histogram_test_count{h_sample="3",type="histogram"} 10
histogram_test_sum{h_sample="1",h_subsample="b",type="histogram"} 100.0
histogram_test_sum{h_sample="1",type="histogram"} 100.0
histogram_test_sum{h_sample="2",type="histogram"} 100.0
histogram_test_sum{h_sample="3",type="histogram"} 100.0
# HELP summary_test A summary.
# TYPE summary_test summary
summary_test_count{s_sample="1",s_subsample="b",type="summary"} 22
summary_test_count{s_sample="1",type="summary"} 250
summary_test_count{s_sample="2",type="summary"} 50
summary_test_count{s_sample="3",type="summary"} 77
summary_test_sum{s_sample="1",s_subsample="b",type="summary"} 98857.0
summary_test_sum{s_sample="1",type="summary"} 374500.0
summary_test_sum{s_sample="2",type="summary"} 124500.0
summary_test_sum{s_sample="3",type="summary"} 269038.0
summary_test{quantile="0.5",s_sample="1",s_subsample="b",type="summary"} 4235.0
summary_test{quantile="0.5",s_sample="1",type="summary"} 1272.0
summary_test{quantile="0.5",s_sample="2",type="summary"} 2260.0
summary_test{quantile="0.5",s_sample="3",type="summary"} 3260.0
summary_test{quantile="0.9",s_sample="1",s_subsample="b",type="summary"} 4470.0
summary_test{quantile="0.9",s_sample="1",type="summary"} 1452.0
summary_test{quantile="0.9",s_sample="2",type="summary"} 2440.0
summary_test{quantile="0.9",s_sample="3",type="summary"} 3442.0
summary_test{quantile="0.99",s_sample="1",s_subsample="b",type="summary"} 4517.0
summary_test{quantile="0.99",s_sample="1",type="summary"} 1496.0
summary_test{quantile="0.99",s_sample="2",type="summary"} 2500.0
summary_test{quantile="0.99",s_sample="3",type="summary"} 3494.0
"""

        with aiohttp.ClientSession(loop=self.loop) as session:
            headers = {ACCEPT: 'text/plain; version=0.0.4'}
            async with session.get(self.metrics_url, headers=headers) as resp:
                assert resp.status == 200
                content = await resp.read()
                self.assertEqual("text/plain; version=0.0.4; charset=utf-8",
                                 resp.headers.get(CONTENT_TYPE))
                self.assertEqual(200, resp.status)
                self.assertEqual(expected_data, content.decode())
