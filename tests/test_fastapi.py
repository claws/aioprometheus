import unittest
from typing import List

import aioprometheus
from aioprometheus import REGISTRY, formats

try:
    from fastapi import FastAPI, Header, Response
    from fastapi.testclient import TestClient

    have_fastapi = True
except ImportError:
    have_fastapi = False


@unittest.skipUnless(have_fastapi, "FastAPI library is not available")
class TestFastAPIRender(unittest.TestCase):
    """
    Test exposing Prometheus metrics from within an FastAPI existing web
    service without starting a separate Prometheus metrics server.
    """

    def tearDown(self):
        REGISTRY.clear()

    def test_render_in_fastapi_app(self):
        """check render usage in FastAPI app"""

        app = FastAPI()
        app.events_counter = aioprometheus.Counter("events", "Number of events.")

        @app.get("/")
        async def hello():
            app.events_counter.inc({"path": "/"})
            return "hello"

        @app.get("/metrics")
        async def handle_metrics(response: Response, accept: List[str] = Header(None)):
            content, http_headers = aioprometheus.render(REGISTRY, accept)
            return Response(content=content, media_type=http_headers["Content-Type"])

        # The test client also starts the web service
        test_client = TestClient(app)

        # Access root to increment metric counter
        response = test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Get text format
        response = test_client.get("/metrics", headers={"accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Get binary format
        response = test_client.get(
            "/metrics",
            headers={"accept": formats.binary.BINARY_CONTENT_TYPE},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.binary.BINARY_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
