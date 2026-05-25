import unittest

from aioprometheus import MetricsMiddleware


async def asgi_app(scope, receive, send):
    pass


class TestASGIMiddleware(unittest.TestCase):
    def test_template_path_falls_back_when_app_has_no_routes(self):
        middleware = MetricsMiddleware(asgi_app)
        middleware.starlette_app = object()

        self.assertEqual(
            middleware.get_full_or_template_path(
                {
                    "type": "http",
                    "root_path": "/api",
                    "path": "/users/1",
                }
            ),
            "/api/users/1",
        )
