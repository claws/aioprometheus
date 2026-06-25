import unittest

from aioprometheus import REGISTRY, Counter, MetricsMiddleware, formats
from aioprometheus.asgi.starlette import metrics

try:
    from fastapi import APIRouter, FastAPI, Request, Response
    from fastapi.testclient import TestClient

    have_fastapi = True
except ImportError:
    have_fastapi = False


@unittest.skipUnless(have_fastapi, "FastAPI library is not available")
class TestFastAPICompatUsage(unittest.TestCase):
    """Test FastAPI compatibility with APIRouter included routes"""

    def tearDown(self):
        REGISTRY.clear()

    def test_included_router_does_not_crash(self):
        """check middleware handles _IncludedRouter nodes in routes"""

        app = FastAPI()
        app.state.users_events_counter = Counter("events", "Number of events.")

        app.add_middleware(MetricsMiddleware)
        app.add_route("/metrics", metrics)

        @app.get("/")
        async def root(request: Request):
            return Response("FastAPI Middleware Example")

        @app.get("/users/{user_id}")
        async def get_user(request: Request, user_id: str):
            request.app.state.users_events_counter.inc(
                {"path": request.scope["path"]}
            )
            return Response(f"{user_id}")

        sub_router = APIRouter(prefix="/sub")

        @sub_router.get("/ping")
        async def ping():
            return Response("pong")

        app.include_router(sub_router)

        test_client = TestClient(app)

        response = test_client.get("/")
        self.assertEqual(response.status_code, 200)

        response = test_client.get("/users/alice")
        self.assertEqual(response.status_code, 200)

        response = test_client.get("/sub/ping")
        self.assertEqual(response.status_code, 200)

        for _ in range(5):
            self.assertEqual(test_client.get("/").status_code, 200)
        for _ in range(5):
            self.assertEqual(test_client.get("/sub/ping").status_code, 200)

    def test_metrics_via_included_router(self):
        """check /metrics is reachable when app has included routers"""

        app = FastAPI()
        app.state.users_events_counter = Counter("events", "Number of events.")

        app.add_middleware(MetricsMiddleware)
        app.add_route("/metrics", metrics)

        @app.get("/")
        async def root(request: Request):
            return Response("FastAPI Middleware Example")

        sub_router = APIRouter(prefix="/sub")

        @sub_router.get("/ping")
        async def ping():
            return Response("pong")

        app.include_router(sub_router)

        test_client = TestClient(app)

        test_client.get("/")
        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            formats.text.TEXT_CONTENT_TYPE,
            response.headers.get("content-type"),
        )

    def test_custom_counter_with_included_router(self):
        """check custom counter appears in /metrics with included routers"""

        app = FastAPI()
        app.state.users_events_counter = Counter("events", "Number of events.")

        app.add_middleware(MetricsMiddleware)
        app.add_route("/metrics", metrics)

        @app.get("/")
        async def root(request: Request):
            return Response("FastAPI Middleware Example")

        @app.get("/users/{user_id}")
        async def get_user(request: Request, user_id: str):
            request.app.state.users_events_counter.inc(
                {"path": request.scope["path"]}
            )
            return Response(f"{user_id}")

        sub_router = APIRouter(prefix="/sub")

        @sub_router.get("/ping")
        async def ping():
            return Response("pong")

        app.include_router(sub_router)

        test_client = TestClient(app)

        test_client.get("/users/charlie")
        response = test_client.get("/metrics", headers={"accept": "*/*"})
        self.assertIn("events", response.text)
        self.assertIn("path", response.text)
