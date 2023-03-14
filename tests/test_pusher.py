import asyncio
import sys
import unittest

from aiohttp_basicauth import BasicAuthMiddleware

from aioprometheus import REGISTRY, Counter, Registry

try:
    import aiohttp
    import aiohttp.web

    from aioprometheus.pusher import Pusher

    have_aiohttp = True
except ImportError:
    have_aiohttp = False


if have_aiohttp:

    class TestPusherServer:
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

        async def slow_handler(self, request):
            await asyncio.sleep(3)
            data = await request.read()
            self.test_results = {
                "path": request.path,
                "headers": request.raw_headers,
                "method": request.method,
                "body": data,
            }
            resp = aiohttp.web.Response(status=200)
            return resp

        async def start(self, addr="127.0.0.1", port=None, middleware=None):
            self._app = aiohttp.web.Application()
            self._app.router.add_route(
                "*", "/metrics/job/{job}{tail:(/.+)?}", self.handler
            )
            self._app.router.add_route("*", "/api/v1/import/prometheus", self.handler)
            self._app.router.add_route("*", "/slow", self.slow_handler)
            if middleware:
                self._app.middlewares.append(middleware)
            self._runner = aiohttp.web.AppRunner(self._app)
            await self._runner.setup()
            self._site = aiohttp.web.TCPSite(self._runner, addr, port)
            await self._site.start()
            # IPV4 returns a 2-Tuple, IPV6 returns a 4-Tuple
            _details = self._site._server.sockets[0].getsockname()
            _host, port = _details[0:2]
            self.port = port
            self.url = f"http://{addr}:{port}"
            # TODO: replace the above with url = self._site.name when aiohttp
            # issue #3018 is resolved.

        async def stop(self):
            await self._runner.cleanup()
            self._site = None
            self._app = None
            self._runner = None


@unittest.skipUnless(have_aiohttp, "aiohttp library is not available")
class TestPusher(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = TestPusherServer()
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()
        REGISTRY.clear()

    async def test_push_job_ping_victoriametrics(self):
        job_name = "my-job"

        # Create a pusher with the path for VictoriaMetrics
        p = Pusher(job_name, self.server.url, path="/api/v1/import/prometheus")
        c = Counter("total_requests", "Total requests.", {})

        c.inc({"url": "/p/user"})

        # Push to the pushgateway
        resp = await p.replace(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/api/v1/import/prometheus", self.server.test_results["path"])

    async def test_push_job_ping(self):
        job_name = "my-job"
        p = Pusher(job_name, self.server.url)
        c = Counter("total_requests", "Total requests.", {})

        c.inc({"url": "/p/user"})

        # Push to the pushgateway
        resp = await p.replace(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])

    async def test_grouping_key(self):
        # See https://github.com/prometheus/pushgateway/blob/master/README.md#url
        # for encoding rules.
        job_name = "my-job"
        p = Pusher(
            job_name,
            self.server.url,
            grouping_key={"instance": "127.0.0.1:1234"},
        )
        c = Counter("total_requests", "Total requests.", {})

        c.inc({})

        # Push to the pushgateway
        resp = await p.replace(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            "/metrics/job/my-job/instance/127.0.0.1:1234",
            self.server.test_results["path"],
        )

    async def test_grouping_key_with_empty_value(self):
        # See https://github.com/prometheus/pushgateway/blob/master/README.md#url
        # for encoding rules.
        job_name = "example"
        p = Pusher(
            job_name,
            self.server.url,
            grouping_key={"first": "", "second": "foo"},
        )
        c = Counter("example_total", "Total examples", {})

        c.inc({})

        # Push to the pushgateway
        resp = await p.replace(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            "/metrics/job/example/first@base64/=/second/foo",
            self.server.test_results["path"],
        )

    async def test_grouping_key_with_value_containing_slash(self):
        # See https://github.com/prometheus/pushgateway/blob/master/README.md#url
        # for encoding rules.
        job_name = "directory_cleaner"
        p = Pusher(
            job_name,
            self.server.url,
            grouping_key={"path": "/var/tmp"},
        )
        c = Counter("exec_total", "Total executions", {})

        c.inc({})

        # Push to the pushgateway
        resp = await p.replace(REGISTRY)
        self.assertEqual(resp.status, 200)

        # Generated base64 content include '=' as padding.
        self.assertEqual(
            "/metrics/job/directory_cleaner/path@base64/L3Zhci90bXA=",
            self.server.test_results["path"],
        )

    async def test_push_add(self):
        job_name = "my-job"
        p = Pusher(job_name, self.server.url)

        counter = Counter("counter_test", "A counter.", {"type": "counter"})

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        [counter.set(c[0], c[1]) for c in counter_data]
        # TextFormatter expected result
        valid_result = (
            b"# HELP counter_test A counter.\n"
            b"# TYPE counter_test counter\n"
            b'counter_test{c_sample="1",c_subsample="b",type="counter"} 400\n'
        )

        # Push to the pushgateway
        resp = await p.add(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
        self.assertEqual("POST", self.server.test_results["method"])
        self.assertEqual(valid_result, self.server.test_results["body"])

    async def test_push_replace(self):
        job_name = "my-job"
        p = Pusher(job_name, self.server.url)

        counter = Counter("counter_test", "A counter.", {"type": "counter"})

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        [counter.set(c[0], c[1]) for c in counter_data]
        # TextFormatter expected result
        valid_result = (
            b"# HELP counter_test A counter.\n"
            b"# TYPE counter_test counter\n"
            b'counter_test{c_sample="1",c_subsample="b",type="counter"} 400\n'
        )

        # Push to the pushgateway
        resp = await p.replace(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
        self.assertEqual("PUT", self.server.test_results["method"])
        self.assertEqual(valid_result, self.server.test_results["body"])

    async def test_push_delete(self):
        job_name = "my-job"
        p = Pusher(job_name, self.server.url)

        counter = Counter("counter_test", "A counter.", {"type": "counter"})

        counter_data = (({"c_sample": "1", "c_subsample": "b"}, 400),)

        [counter.set(c[0], c[1]) for c in counter_data]
        # TextFormatter expected result
        valid_result = (
            b"# HELP counter_test A counter.\n"
            b"# TYPE counter_test counter\n"
            b'counter_test{c_sample="1",c_subsample="b",type="counter"} 400\n'
        )

        # Push to the pushgateway
        resp = await p.delete(REGISTRY)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
        self.assertEqual("DELETE", self.server.test_results["method"])
        self.assertEqual(valid_result, self.server.test_results["body"])

    @unittest.skipUnless(sys.version_info > (3, 8, 0), "requires 3.8+")
    async def test_push_timeout(self):
        job_name = "my-job"
        p = Pusher(job_name, self.server.url, path="/slow")

        counter = Counter("counter_test", "A counter.")
        counter.inc({})

        try:
            import asyncio.exceptions
        except:
            self.skipTest("requires python 3.8+")
            return

        timeout = aiohttp.ClientTimeout(total=0.5)
        with self.assertRaises(asyncio.exceptions.TimeoutError):
            await p.delete(REGISTRY, timeout=timeout)

        with self.assertRaises(asyncio.exceptions.TimeoutError):
            await p.replace(REGISTRY, timeout=timeout)

        with self.assertRaises(asyncio.exceptions.TimeoutError):
            await p.add(REGISTRY, timeout=timeout)

        with self.assertRaises(asyncio.exceptions.TimeoutError):
            await p.replace(REGISTRY, timeout=timeout)


@unittest.skipUnless(have_aiohttp, "aiohttp library is not available")
class TestPusherBasicAuth(unittest.IsolatedAsyncioTestCase):
    """A minimal duplicate of the test suite above that demonstrates auth used with Pusher"""

    async def asyncSetUp(self):
        self.username = "Joe"
        self.password = "4321"
        self.server = TestPusherServer()
        bam = BasicAuthMiddleware(username=self.username, password=self.password)
        await self.server.start(middleware=bam)

    async def asyncTearDown(self):
        await self.server.stop()
        REGISTRY.clear()

    async def test_push_job_ping_with_auth(self):
        job_name = "my-job"
        p = Pusher(job_name, self.server.url)
        c = Counter("total_requests", "Total requests.", {})

        c.inc({"url": "/p/user"})

        self.auth = aiohttp.BasicAuth(self.username, password=self.password)

        # Push to the pushgateway
        resp = await p.replace(REGISTRY, auth=self.auth)
        self.assertEqual(resp.status, 200)

        self.assertEqual("/metrics/job/my-job", self.server.test_results["path"])
