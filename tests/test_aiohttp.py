import unittest

from aioprometheus import REGISTRY, Counter, formats, render

try:
    import aiohttp
    import aiohttp.hdrs
    import aiohttp.web

    have_aiohttp = True
except ImportError:
    have_aiohttp = False


@unittest.skipUnless(have_aiohttp, "aiohttp library is not available")
class TestAiohttpRender(unittest.IsolatedAsyncioTestCase):
    """
    Test exposing Prometheus metrics from within a aiohttp existing web
    service without starting a separate Prometheus metrics server.
    """

    def tearDown(self):
        REGISTRY.clear()

    async def test_text_render_in_aiohttp_app(self):
        """check text render usage in aiohttp app"""

        app = aiohttp.web.Application()
        app.registry = REGISTRY
        app.events_counter = Counter("events", "Number of events.")

        async def index(request):
            app.events_counter.inc({"path": "/"})
            return aiohttp.web.Response(text="hello")

        async def handle_metrics(request):
            content, http_headers = render(
                app.registry, request.headers.getall(aiohttp.hdrs.ACCEPT, [])
            )
            return aiohttp.web.Response(body=content, headers=http_headers)

        app.add_routes(
            [aiohttp.web.get("/", index), aiohttp.web.get("/metrics", handle_metrics)]
        )

        runner = aiohttp.web.AppRunner(app, shutdown_timeout=1.0)
        await runner.setup()

        site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()

        # Fetch ephemeral port that was bound.
        # IPv4 address returns a 2-tuple, IPv6 returns a 4-tuple
        host, port, *_ = runner.addresses[0]
        host = host if ":" not in host else f"[{host}]"
        url = f"http://{host}:{port}"
        root_url = f"{url}/"
        metrics_url = f"{url}/metrics"

        async with aiohttp.ClientSession() as session:
            # Access root to increment metric counter
            async with session.get(root_url) as response:
                self.assertEqual(response.status, 200)

            # Get default format
            async with session.get(
                metrics_url, headers={aiohttp.hdrs.ACCEPT: "*/*"}
            ) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(
                    formats.text.TEXT_CONTENT_TYPE,
                    response.headers.get("content-type"),
                )
                # content = await response.read()

            # Get text format
            async with session.get(
                metrics_url, headers={aiohttp.hdrs.ACCEPT: "text/plain;"}
            ) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(
                    formats.text.TEXT_CONTENT_TYPE,
                    response.headers.get("content-type"),
                )

        await runner.cleanup()
