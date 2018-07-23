import asynctest
import aiohttp
import aiohttp.hdrs
import aiohttp.web
import unittest
import aioprometheus


class TestAiohttpRender(asynctest.TestCase):
    """
    Test exposing Prometheus metrics from within a aiohttp existing web
    service without starting a separate Prometheus metrics server.
    """

    async def test_render_in_aiohttp_app(self):
        """ check render usage in aiohttp app """

        app = aiohttp.web.Application()
        app.registry = aioprometheus.Registry()
        app.events_counter = aioprometheus.Counter("events", "Number of events.")
        app.registry.register(app.events_counter)

        async def index(request):
            app.events_counter.inc({"path": "/"})
            return aiohttp.web.Response(text="hello")

        async def handle_metrics(request):
            content, http_headers = aioprometheus.render(
                app.registry, request.headers.getall(aiohttp.hdrs.ACCEPT, [])
            )
            return aiohttp.web.Response(body=content, headers=http_headers)

        app.add_routes(
            [aiohttp.web.get("/", index), aiohttp.web.get("/metrics", handle_metrics)]
        )

        runner = aiohttp.web.AppRunner(app)
        await runner.setup()

        site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0, shutdown_timeout=1.0)
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
                    aioprometheus.formats.TEXT_CONTENT_TYPE,
                    response.headers.get("content-type"),
                )
                # content = await response.read()

            # Get text format
            async with session.get(
                metrics_url, headers={aiohttp.hdrs.ACCEPT: "text/plain;"}
            ) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(
                    aioprometheus.formats.TEXT_CONTENT_TYPE,
                    response.headers.get("content-type"),
                )

            # Get binary format
            async with session.get(
                metrics_url,
                headers={
                    aiohttp.hdrs.ACCEPT: aioprometheus.formats.BINARY_CONTENT_TYPE
                },
            ) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(
                    aioprometheus.formats.BINARY_CONTENT_TYPE,
                    response.headers.get("content-type"),
                )

        await runner.cleanup()
