
import asyncio

import aiohttp

from aioprometheus import Counter, Pusher, Registry
from aioprometheus.test_utils import AsyncioTestCase


TEST_PORT = 61423
TEST_HOST = "127.0.0.1"
TEST_URL = "http://{host}:{port}".format(host=TEST_HOST, port=TEST_PORT)


class TestPusherServer(object):
    ''' This fixture class acts as the Push Gateway.

    It handles requests and stores various request attributes in the
    test_results attribute which is later checked in tests.
    '''

    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.test_results = None

    async def handler(self, request):
        data = await request.read()
        self.test_results = {
            'path': request.path,
            'headers': request.raw_headers,
            'method': request.method,
            'body': data}
        resp = aiohttp.web.Response(status=200)
        return resp

    async def start(self, addr='', port=TEST_PORT):
        self._svc = aiohttp.web.Application()
        self._svc.router.add_route(
            '*',
            "/metrics/job/{job}",
            self.handler)
        self._handler = self._svc.make_handler()
        self._svr = await self.loop.create_server(
            self._handler, addr, port)

    async def stop(self):
        self._svr.close()
        await self._svr.wait_closed()
        await self._svc.shutdown()
        await self._handler.finish_connections(1.0)
        await self._svc.cleanup()
        self._svr = None
        self._svc = None
        self._handler = None


def expected_job_path(job):
    return Pusher.PATH.format(job)


class TestPusher(AsyncioTestCase):

    async def setUp(self):
        self.server = TestPusherServer(loop=self.loop)
        await self.server.start()

    async def tearDown(self):
        await self.server.stop()

    async def test_push_job_ping(self):
        job_name = "my-job"
        p = Pusher(job_name, TEST_URL, loop=self.loop)
        registry = Registry()
        c = Counter("total_requests", "Total requests.", {})
        registry.register(c)

        c.inc({'url': "/p/user", })

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            expected_job_path(job_name),
            self.server.test_results['path'])

    async def test_push_add(self):
        job_name = "my-job"
        p = Pusher(job_name, TEST_URL)
        registry = Registry()
        counter = Counter("counter_test", "A counter.", {'type': "counter"})
        registry.register(counter)

        counter_data = (
            ({'c_sample': '1', 'c_subsample': 'b'}, 400),
        )

        [counter.set(c[0], c[1]) for c in counter_data]
        valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n\r'
                        b'\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample\x12'
                        b'\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t\x00'
                        b'\x00\x00\x00\x00\x00y@')

        # Push to the pushgateway
        resp = await p.add(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            expected_job_path(job_name),
            self.server.test_results['path'])
        self.assertEqual("POST", self.server.test_results['method'])
        self.assertEqual(valid_result, self.server.test_results['body'])

    async def test_push_replace(self):
        job_name = "my-job"
        p = Pusher(job_name, TEST_URL)
        registry = Registry()
        counter = Counter("counter_test", "A counter.", {'type': "counter"})
        registry.register(counter)

        counter_data = (
            ({'c_sample': '1', 'c_subsample': 'b'}, 400),
        )

        [counter.set(c[0], c[1]) for c in counter_data]
        valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n\r'
                        b'\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample\x12'
                        b'\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t\x00'
                        b'\x00\x00\x00\x00\x00y@')

        # Push to the pushgateway
        resp = await p.replace(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            expected_job_path(job_name),
            self.server.test_results['path'])
        self.assertEqual("PUT", self.server.test_results['method'])
        self.assertEqual(valid_result, self.server.test_results['body'])

    async def test_push_delete(self):
        job_name = "my-job"
        p = Pusher(job_name, TEST_URL)
        registry = Registry()
        counter = Counter("counter_test", "A counter.", {'type': "counter"})
        registry.register(counter)

        counter_data = (
            ({'c_sample': '1', 'c_subsample': 'b'}, 400),
        )

        [counter.set(c[0], c[1]) for c in counter_data]
        valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n'
                        b'\r\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample'
                        b'\x12\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t'
                        b'\x00\x00\x00\x00\x00\x00y@')

        # Push to the pushgateway
        resp = await p.delete(registry)
        self.assertEqual(resp.status, 200)

        self.assertEqual(
            expected_job_path(job_name),
            self.server.test_results['path'])
        self.assertEqual("DELETE", self.server.test_results['method'])
        self.assertEqual(valid_result, self.server.test_results['body'])
