import asynctest
import unittest
import aioprometheus

try:
    from vibora import Vibora, Request, Response

    have_vibora = True
except ImportError:
    have_vibora = False


@unittest.skipUnless(have_vibora, "Vibora library is not available")
class TestViboraRender(asynctest.TestCase):
    """
    Test exposing Prometheus metrics from within an Vibora existing web
    service without starting a separate Prometheus metrics server.
    """

    async def test_render_in_vibora_app(self):
        """ check render usage in Vibora app """

        app = Vibora(__name__)
        app.registry = aioprometheus.Registry()
        app.events_counter = aioprometheus.Counter("events", "Number of events.")
        app.registry.register(app.events_counter)

        @app.route("/")
        async def index(request: Request):
            app.events_counter.inc({"path": "/"})
            return Response(b"hello")

        @app.route("/metrics")
        async def handle_metrics(request: Request):
            """
            Negotiate a response format by inspecting the ACCEPTS headers and selecting
            the most efficient format. Render metrics in the registry into the chosen
            format and return a response.
            """
            content, http_headers = aioprometheus.render(
                app.registry, [request.headers.get("accept")]
            )
            return Response(content, headers=http_headers)

        # NOTE: Vibora client.get HTTP headers handling seem to expect case-sensitive.
        # Must use Accept and not accept or ACCEPT! Where as response handling of
        # requests doesn't seem to care.
        # Until Vibora #139 is resolved we must use "Accept".

        # The test client also starts the web service
        client = app.test_client()

        # Access root to increment metric counter
        response = await client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = await client.get("/metrics", headers={"Accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            aioprometheus.formats.TEXT_CONTENT_TYPE,
            [response.headers.get("Content-Type")],
        )

        # Get text format
        response = await client.get("/metrics", headers={"Accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            aioprometheus.formats.TEXT_CONTENT_TYPE,
            [response.headers.get("content-type")],
        )

        # # Get binary format
        response = await client.get(
            "/metrics", headers={"Accept": aioprometheus.formats.BINARY_CONTENT_TYPE}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            aioprometheus.formats.BINARY_CONTENT_TYPE,
            [response.headers.get("content-type")],
        )
