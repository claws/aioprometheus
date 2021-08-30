import asyncio

import aiohttp
import asynctest

from aioprometheus import Counter, Registry, pusher


class TestPusherServer(object):
    """This fixture class acts as the Push Gateway.

    It handles requests and stores various request attributes in the
    test_results attribute which is later checked in tests.
    """

    def __init__(self):
        self.test_results = None

    async def handler(self, request):
        data = await request.read()
        self.test_results = {
            "path": request.path,
            "headers": request.raw_headers,
            "method": request.method,
            "body": data,
        }
        resp = aiohttp.web.Response(status=200)
        return resp

    async def start(self, addr="127.0.0.1", port=None):
        self._app = aiohttp.web.Application()
        self._app.router.add_route("*", "/metrics/job/{job}{tail:(/.+)?}", self.handler)
        self._app.router.add_route("*", "/api/v1/import/prometheus", self.handler)
        self._runner = aiohttp.web.AppRunner(self._app)
        await self._runner.setup()
        self._site = aiohttp.web.TCPSite(self._runner, addr, port)
        await self._site.start()
        # IPV4 returns a 2-Tuple, IPV6 returns a 4-Tuple
        _details = self._site._server.sockets[0].getsockname()
        _host, _port = _details[0:2]
        self.port = _port
        self.url = f"http://{addr}:{_port}"
        # TODO: replace the above with url = self._site.name when aiohttp
        # issue #3018 is resolved.

    async def stop(self):
        await self._runner.cleanup()
        self._site = None
        self._app = None
        self._runner = None


class TestPusher(asynctest.TestCase):
    async def setUp(self):
        self.server = TestPusherServer()
        await self.server.start()

    async def tearDown(self):
        await self.server.stop()

    async def test_push_job_ping_victoriametrics(self):
        job_name = "my-job"

        # Create a pusher with the path for VictoriaMetrics
        p = pusher.Pusher(job_name, self.server.url, path="/api/v1/import/prometheus")
        registry = Registry()
        c = Counter("total_requests", "Total requests.", {})
        registry.register(c)

        c.inc({"url": "/p/user"})

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/api/v1/import/prometheus", self.server.test_results["path"])

    async def test_push_job_ping(self):
        job_name = "my-job"
        p = pusher.Pusher(job_name, self.server.url)
        registry = Registry()
        c = Counter("total_requests", "Total requests.", {})
        registry.register(c)

        c.inc({"url": "/p/user"})

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])

    async def test_grouping_key(self):
        # See https://github.com/prometheus/pushgateway/blob/master/README.md#url
        # for encoding rules.
        job_name = "my-job"
        p = pusher.Pusher(
            job_name,
            self.server.url,
            grouping_key={"instance": "127.0.0.1:1234"},
        )
        registry = Registry()
        c = Counter("total_requests", "Total requests.", {})
        registry.register(c)

        c.inc({})

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            "/metrics/job/my-job/instance/127.0.0.1:1234",
            self.server.test_results["path"],
        )

    async def test_grouping_key_with_empty_value(self):
        # See https://github.com/prometheus/pushgateway/blob/master/README.md#url
        # for encoding rules.
        job_name = "example"
        p = pusher.Pusher(
            job_name,
            self.server.url,
            grouping_key={"first": "", "second": "foo"},
        )
        registry = Registry()
        c = Counter("example_total", "Total examples", {})
        registry.register(c)

        c.inc({})

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            "/metrics/job/example/first@base64/=/second/foo",
            self.server.test_results["path"],
        )

    async def test_grouping_key_with_value_containing_slash(self):
        # See https://github.com/prometheus/pushgateway/blob/master/README.md#url
        # for encoding rules.
        job_name = "directory_cleaner"
        p = pusher.Pusher(
            job_name,
            self.server.url,
            grouping_key={"path": "/var/tmp"},
        )
        registry = Registry()
        c = Counter("exec_total", "Total executions", {})
        registry.register(c)

        c.inc({})

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        # Generated base64 content include '=' as padding.
        self.assertEqual(
            "/metrics/job/directory_cleaner/path@base64/L3Zhci90bXA=",
            self.server.test_results["path"],
        )

    async def test_push_add(self):
        job_name = "my-job"
        p = pusher.Pusher(job_name, self.server.url)
        registry = Registry()
        counter = Counter("counter_test", "A counter.", {"type": "counter"})
        registry.register(counter)

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        [counter.set(c[0], c[1]) for c in counter_data]
        # TextFormatter expected result
        valid_result = (
            b"# HELP counter_test A counter.\n"
            b"# TYPE counter_test counter\n"
            b'counter_test{c_sample="1",c_subsample="b",type="counter"} 400\n'
        )
        # BinaryFormatter expected result
        # valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n\r'
        #                 b'\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample\x12'
        #                 b'\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t\x00'
        #                 b'\x00\x00\x00\x00\x00y@')

        # Push to the pushgateway
        resp = await p.add(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
        self.assertEqual("POST", self.server.test_results["method"])
        self.assertEqual(valid_result, self.server.test_results["body"])

    async def test_push_replace(self):
        job_name = "my-job"
        p = pusher.Pusher(job_name, self.server.url)
        registry = Registry()
        counter = Counter("counter_test", "A counter.", {"type": "counter"})
        registry.register(counter)

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        [counter.set(c[0], c[1]) for c in counter_data]
        # TextFormatter expected result
        valid_result = (
            b"# HELP counter_test A counter.\n"
            b"# TYPE counter_test counter\n"
            b'counter_test{c_sample="1",c_subsample="b",type="counter"} 400\n'
        )
        # BinaryFormatter expected result
        # valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n\r'
        #                 b'\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample\x12'
        #                 b'\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t\x00'
        #                 b'\x00\x00\x00\x00\x00y@')

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
        self.assertEqual("PUT", self.server.test_results["method"])
        self.assertEqual(valid_result, self.server.test_results["body"])

    async def test_push_delete(self):
        job_name = "my-job"
        p = pusher.Pusher(job_name, self.server.url)
        registry = Registry()
        counter = Counter("counter_test", "A counter.", {"type": "counter"})
        registry.register(counter)

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        [counter.set(c[0], c[1]) for c in counter_data]
        # TextFormatter expected result
        valid_result = (
            b"# HELP counter_test A counter.\n"
            b"# TYPE counter_test counter\n"
            b'counter_test{c_sample="1",c_subsample="b",type="counter"} 400\n'
        )
        # BinaryFormatter expected result
        # valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n'
        #                 b'\r\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample'
        #                 b'\x12\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t'
        #                 b'\x00\x00\x00\x00\x00\x00y@')

        # Push to the pushgateway
        resp = await p.delete(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
        self.assertEqual("DELETE", self.server.test_results["method"])
        self.assertEqual(valid_result, self.server.test_results["body"])
