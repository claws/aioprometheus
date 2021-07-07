import unittest

import asynctest

import aioprometheus

try:
    from quart import Quart, request

    have_quart = True
except ImportError:
    have_quart = False


@unittest.skipUnless(have_quart, "Quart library is not available")
class TestQuartRender(asynctest.TestCase):
    """
    Test exposing Prometheus metrics from within an Quart existing web
    service without starting a separate Prometheus metrics server.
    """

    async def test_render_in_quart_app(self):
        """check render usage in Quart app"""

        app = Quart(__name__)
        app.registry = aioprometheus.Registry()
        app.events_counter = aioprometheus.Counter("events", "Number of events.")
        app.registry.register(app.events_counter)

        @app.route("/")
        async def index():
            app.events_counter.inc({"path": "/"})
            return "hello"

        @app.route("/metrics")
        async def handle_metrics():
            content, http_headers = aioprometheus.render(
                app.registry, request.headers.getlist("accept")
            )
            return content, http_headers

        # The test client also starts the web service
        test_client = app.test_client()

        # Access root to increment metric counter
        response = await test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = await test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            aioprometheus.formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
        # payload = await response.get_data()

        # Get text format
        response = await test_client.get("/metrics", headers={"accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            aioprometheus.formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Get binary format
        response = await test_client.get(
            "/metrics",
            headers={"accept": aioprometheus.formats.binary.BINARY_CONTENT_TYPE},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            aioprometheus.formats.binary.BINARY_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
