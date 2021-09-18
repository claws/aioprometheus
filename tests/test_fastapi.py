import unittest
from typing import List

from aioprometheus import REGISTRY, Counter, MetricsMiddleware, formats, render
from aioprometheus.asgi.starlette import metrics

try:
    from fastapi import FastAPI, Header, Request, Response
    from fastapi.testclient import TestClient

    have_fastapi = True
except ImportError:
    have_fastapi = False

try:
    import prometheus_metrics_proto as pmp

    have_pmp = True
except ImportError:
    have_pmp = False


@unittest.skipUnless(have_fastapi, "FastAPI library is not available")
class TestFastAPIUsage(unittest.TestCase):
    """Test exposing Prometheus metrics from within a FastAPI app"""

    def tearDown(self):
        REGISTRY.clear()

    def test_render_text(self):
        """check render text usage in FastAPI app"""

        app = FastAPI()
        app.events_counter = Counter("events", "Number of events.")

        @app.get("/")
        async def hello():
            app.events_counter.inc({"path": "/"})
            return "hello"

        @app.get("/metrics")
        async def handle_metrics(response: Response, accept: List[str] = Header(None)):
            content, http_headers = render(REGISTRY, accept)
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

        # Check content
        self.assertIn('events{path="/"} 1', response.text)

    @unittest.skipUnless(have_pmp, "prometheus_metrics_proto library is not available")
    def test_render_binary(self):
        """check render binary usage in FastAPI app"""

        app = FastAPI()
        app.events_counter = Counter("events", "Number of events.")

        @app.get("/")
        async def hello():
            app.events_counter.inc({"path": "/"})
            return "hello"

        @app.get("/metrics")
        async def handle_metrics(response: Response, accept: List[str] = Header(None)):
            content, http_headers = render(REGISTRY, accept)
            return Response(content=content, media_type=http_headers["Content-Type"])

        # The test client also starts the web service
        test_client = TestClient(app)

        # Access root to increment metric counter
        response = test_client.get("/")
        self.assertEqual(response.status_code, 200)

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

        metrics = pmp.decode(response.content)
        self.assertEqual(len(metrics), 1)
        mf = metrics[0]
        self.assertIsInstance(mf, pmp.MetricFamily)
        self.assertEqual(mf.type, pmp.COUNTER)
        self.assertEqual(len(mf.metric), 1)
        self.assertEqual(mf.metric[0].counter.value, 1)
        self.assertEqual(mf.metric[0].label[0].name, "path")
        self.assertEqual(mf.metric[0].label[0].value, "/")

    def test_asgi_middleware(self):
        """check ASGI middleware usage in FastAPI app"""

        app = FastAPI()

        # Add a custom application metric so it can be checked in output
        app.events_counter = Counter("events", "Number of events.")

        @app.get("/")
        async def hello():
            app.events_counter.inc({"path": "/"})
            return "hello"

        # Add a template path so it can be checked in output
        @app.get("/users/{user_id}")
        async def get_user(user_id: str):
            return f"{user_id}"

        # Add a route that always generates an exception
        @app.get("/boom")
        async def hello():
            raise Exception("Boom")

        app.add_middleware(MetricsMiddleware)
        app.add_route("/metrics", metrics)

        # The test client also starts the web service
        test_client = TestClient(app)

        # The test client does not call the ASGI lifespan scope on the app
        # so we need to manual set the starlette_app attribute on the middleware.
        # The only way I can think of doing this is to walk over the middlewares.
        # However the structure is difficult to walk over.
        # 'sem' represents the ServerErrorMiddleware that Starlette always adds
        # as the first Middlware, before any user middleware.
        sem = app.middleware_stack
        self.assertIsInstance(sem.app, MetricsMiddleware)
        sem.app.starlette_app = app

        # Access root to update default metrics and trigger custom metric update
        response = test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Access templated path
        response = test_client.get("/users/bob")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Check content
        self.assertIn('events{path="/"} 1', response.text)

        self.assertIn('requests_total_counter{method="GET",path="/"} 1', response.text)
        self.assertIn(
            'status_codes_counter{method="GET",path="/",status_code="200"} 1',
            response.text,
        )
        self.assertIn('responses_total_counter{method="GET",path="/"} 1', response.text)

        self.assertIn(
            'requests_total_counter{method="GET",path="/users/{user_id}"} 1',
            response.text,
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/users/{user_id}",status_code="200"} 1',
            response.text,
        )
        self.assertIn(
            'responses_total_counter{method="GET",path="/users/{user_id}"} 1',
            response.text,
        )

        # Access it again to confirm default metrics get incremented
        response = test_client.get("/")
        self.assertEqual(response.status_code, 200)

        # Access a different template path so we can confirm only the template
        # path value gets incremented.
        response = test_client.get("/users/alice")
        self.assertEqual(response.status_code, 200)

        # Get text format
        response = test_client.get("/metrics", headers={"accept": "text/plain;"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Check content
        self.assertIn('events{path="/"} 2', response.text)

        self.assertIn('requests_total_counter{method="GET",path="/"} 2', response.text)
        self.assertIn(
            'status_codes_counter{method="GET",path="/",status_code="200"} 2',
            response.text,
        )
        self.assertIn('responses_total_counter{method="GET",path="/"} 2', response.text)

        self.assertIn(
            'requests_total_counter{method="GET",path="/users/{user_id}"} 2',
            response.text,
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/users/{user_id}",status_code="200"} 2',
            response.text,
        )
        self.assertIn(
            'responses_total_counter{method="GET",path="/users/{user_id}"} 2',
            response.text,
        )

        # Confirm no exception have been observed so far.
        self.assertNotIn("exceptions_total_counter{", response.text)

        # Access boom route to trigger exception metric update
        with self.assertRaises(Exception):
            response = test_client.get("/boom")
            self.assertEqual(response.status_code, 500)

        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Check exception counter was incremented
        self.assertIn(
            'exceptions_total_counter{method="GET",path="/boom"} 1', response.text
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/boom",status_code="500"} 1',
            response.text,
        )

    def test_asgi_middleware_template_path_disabled(self):
        """check ASGI middleware template path usage in FastAPI app"""

        app = FastAPI()

        app.add_middleware(MetricsMiddleware, use_template_urls=False)
        app.add_route("/metrics", metrics)

        @app.get("/users/{user_id}")
        async def get_user(user_id: str):
            return f"{user_id}"

        # The test client also starts the web service
        test_client = TestClient(app)

        # Access root to increment metric counter
        response = test_client.get("/users/bob")
        self.assertEqual(response.status_code, 200)

        # Get default format
        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Check content
        self.assertIn(
            'requests_total_counter{method="GET",path="/users/bob"} 1', response.text
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/users/bob",status_code="200"} 1',
            response.text,
        )
        self.assertIn(
            'responses_total_counter{method="GET",path="/users/bob"} 1', response.text
        )

        # Access it again to confirm default metrics get incremented
        response = test_client.get("/users/alice")
        self.assertEqual(response.status_code, 200)

        # Get text format
        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

        # Check content
        self.assertIn(
            'requests_total_counter{method="GET",path="/users/bob"} 1', response.text
        )
        self.assertIn(
            'requests_total_counter{method="GET",path="/users/alice"} 1', response.text
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/users/bob",status_code="200"} 1',
            response.text,
        )
        self.assertIn(
            'status_codes_counter{method="GET",path="/users/alice",status_code="200"} 1',
            response.text,
        )
        self.assertIn(
            'responses_total_counter{method="GET",path="/users/bob"} 1', response.text
        )
        self.assertIn(
            'responses_total_counter{method="GET",path="/users/alice"} 1', response.text
        )
