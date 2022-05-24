import logging
import sys
import unittest

import asynctest

from aioprometheus import REGISTRY, Counter, MetricsMiddleware, formats, render

try:
    from quart import Quart, request

    from aioprometheus.asgi.quart import metrics

    have_quart = True
except ImportError:
    have_quart = False

try:
    import prometheus_metrics_proto as pmp

    have_pmp = True
except ImportError:
    have_pmp = False


@unittest.skipUnless(have_quart, "Quart library is not available")
class TestQuartRender(asynctest.TestCase):
    """Test exposing Prometheus metrics from within a Quart app"""

    def tearDown(self):
        REGISTRY.clear()

    async def test_render_text(self):
        """check render text usage in Quart app"""

        app = Quart(__name__)
        app.events_counter = Counter("events", "Number of events.")

        @app.route("/")
        async def index():
            app.events_counter.inc({"path": "/"})
            return "hello"

        @app.route("/metrics")
        async def handle_metrics():
            content, http_headers = render(REGISTRY, request.headers.getlist("accept"))
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
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Get text format
        response = await test_client.get("/metrics", headers={"accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        payload = await response.get_data()

        # Check content
        self.assertIn(b'events{path="/"} 1', payload)

    @unittest.skipUnless(have_pmp, "prometheus_metrics_proto library is not available")
    async def test_render_binary(self):
        """check render binary usage in Quart app"""

        app = Quart(__name__)
        app.events_counter = Counter("events", "Number of events.")

        @app.route("/")
        async def index():
            app.events_counter.inc({"path": "/"})
            return "hello"

        @app.route("/metrics")
        async def handle_metrics():
            content, http_headers = render(REGISTRY, request.headers.getlist("accept"))
            return content, http_headers

        # The test client also starts the web service
        test_client = app.test_client()

        # Access root to increment metric counter
        response = await test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get binary format
        response = await test_client.get(
            "/metrics",
            headers={"accept": formats.binary.BINARY_CONTENT_TYPE},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.binary.BINARY_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        payload = await response.get_data()
        metrics = pmp.decode(payload)
        self.assertEqual(len(metrics), 1)
        mf = metrics[0]
        self.assertIsInstance(mf, pmp.MetricFamily)
        self.assertEqual(mf.type, pmp.COUNTER)
        self.assertEqual(len(mf.metric), 1)
        self.assertEqual(mf.metric[0].counter.value, 1)
        self.assertEqual(mf.metric[0].label[0].name, "path")
        self.assertEqual(mf.metric[0].label[0].value, "/")

    async def test_asgi_middleware(self):
        """check ASGI middleware usage in Quart app"""

        app = Quart(__name__)
        app.events_counter = Counter("events", "Number of events.")

        @app.route("/")
        async def index():
            app.events_counter.inc({"path": "/"})
            return "hello"

        # Add a route that always generates an exception
        @app.route("/boom")
        async def hello():
            raise Exception("Boom")

        app.asgi_app = MetricsMiddleware(app.asgi_app)
        app.add_url_rule("/metrics", "metrics", metrics, methods=["GET"])

        # The test client also starts the web service
        test_client = app.test_client()

        # Access root to increment metric counter
        response = await test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = await test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
        payload = await response.get_data()
        content = payload.decode("utf-8")

        # Check content
        self.assertIn('events{path="/"} 1', content)
        self.assertIn('requests_total_counter{method="GET",path="/"} 1', content)
        self.assertIn(
            'status_codes_counter{method="GET",path="/",status_code="200"} 1', content
        )
        self.assertIn('responses_total_counter{method="GET",path="/"} 1', content)

        # Access it again to confirm default metrics get incremented
        response = await test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get text format
        response = await test_client.get("/metrics", headers={"accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        payload = await response.get_data()
        content = payload.decode("utf-8")

        # Check content
        self.assertIn('events{path="/"} 2', content)
        self.assertIn('requests_total_counter{method="GET",path="/"} 2', content)
        self.assertIn(
            'status_codes_counter{method="GET",path="/",status_code="200"} 2', content
        )
        self.assertIn('responses_total_counter{method="GET",path="/"} 2', content)

        # Confirm no exception have been observed so far.
        self.assertNotIn("exceptions_total_counter{", content)

        # Access boom route to trigger exception metric update.
        # Silence the stderr output log generated by Quart when it captures
        # the exception.
        with self.assertLogs("quart.app", logging.ERROR):
            with asynctest.mock.patch.object(sys.stderr, "write") as mock_stderr:
                response = await test_client.get("/boom")
                self.assertEqual(response.status_code, 500)

        response = await test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
        payload = await response.get_data()
        content = payload.decode("utf-8")

        # Check exception counter was NOT incremented due to Quart not
        # propagating exceptions out to the ASGI layer.
        self.assertNotIn(
            'exceptions_total_counter{method="GET",path="/boom"} 1', content
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/boom",status_code="500"} 1',
            content,
        )

    async def test_asgi_middleware_group_status_codes_enabled(self):
        """check ASGI middleware group status codes usage in FastAPI app"""

        app = Quart(__name__)
        app.events_counter = Counter("events", "Number of events.")

        @app.route("/")
        async def index():
            app.events_counter.inc({"path": "/"})
            return "hello"

        # Add a route that always generates an exception
        @app.route("/boom")
        async def hello():
            raise Exception("Boom")

        app.asgi_app = MetricsMiddleware(app.asgi_app, group_status_codes=True)
        app.add_url_rule("/metrics", "metrics", metrics, methods=["GET"])

        # The test client also starts the web service
        test_client = app.test_client()

        # Access root to increment metric counter
        response = await test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = await test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
        payload = await response.get_data()
        content = payload.decode("utf-8")

        # Check content
        self.assertIn('events{path="/"} 1', content)
        self.assertIn('requests_total_counter{method="GET",path="/"} 1', content)
        self.assertIn(
            'status_codes_counter{method="GET",path="/",status_code="2xx"} 1', content
        )
        self.assertIn('responses_total_counter{method="GET",path="/"} 1', content)

        # Access it again to confirm default metrics get incremented
        response = await test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Get text format
        response = await test_client.get("/metrics", headers={"accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        payload = await response.get_data()
        content = payload.decode("utf-8")

        # Check content
        self.assertIn('events{path="/"} 2', content)
        self.assertIn('requests_total_counter{method="GET",path="/"} 2', content)
        self.assertIn(
            'status_codes_counter{method="GET",path="/",status_code="2xx"} 2', content
        )
        self.assertIn('responses_total_counter{method="GET",path="/"} 2', content)

        # Confirm no exception have been observed so far.
        self.assertNotIn("exceptions_total_counter{", content)

        # Access boom route to trigger exception metric update.
        # Silence the stderr output log generated by Quart when it captures
        # the exception.
        with self.assertLogs("quart.app", logging.ERROR):
            with asynctest.mock.patch.object(sys.stderr, "write") as mock_stderr:
                response = await test_client.get("/boom")
                self.assertEqual(response.status_code, 500)

        response = await test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )
        payload = await response.get_data()
        content = payload.decode("utf-8")

        # Check exception counter was NOT incremented due to Quart not
        # propagating exceptions out to the ASGI layer.
        self.assertNotIn(
            'exceptions_total_counter{method="GET",path="/boom"} 1', content
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/boom",status_code="5xx"} 1',
            content,
        )
