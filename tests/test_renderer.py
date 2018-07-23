import asynctest
import aioprometheus


class TestRenderer(asynctest.TestCase):
    async def test_invalid_registry(self):
        """ check only valid registry can be provided """
        for invalid_registry in ["nope", dict(), list()]:
            with self.assertRaises(Exception) as cm:
                aioprometheus.render(invalid_registry, [])
            self.assertIn("registry must be a Registry, got:", str(cm.exception))

    async def test_invalid_accepts_headers(self):
        """ check only valid accepts_headers types can be provided """
        registry = aioprometheus.Registry()
        for accepts_headers in ["nope", None, 42, dict()]:
            with self.assertRaises(Exception) as cm:
                aioprometheus.render(registry, accepts_headers)
            self.assertIn("accepts_headers must be a sequence, got:", str(cm.exception))

    async def test_render_default(self):
        """ check metrics can be rendered using default format """
        accepts_headers = ("application/json", "*/*", "application/nothing")
        registry = aioprometheus.Registry()
        content, http_headers = aioprometheus.render(registry, accepts_headers)
        self.assertEqual(
            http_headers["Content-Type"], aioprometheus.formats.TEXT_CONTENT_TYPE
        )

    async def test_render_text(self):
        """ check metrics can be rendered using text format """
        accepts_headers = ("text/plain;",)
        registry = aioprometheus.Registry()
        content, http_headers = aioprometheus.render(registry, accepts_headers)
        self.assertEqual(
            http_headers["Content-Type"], aioprometheus.formats.TEXT_CONTENT_TYPE
        )

    async def test_render_binary(self):
        """ check metrics can be rendered using binary format """
        accepts_headers = (aioprometheus.formats.BINARY_CONTENT_TYPE,)
        registry = aioprometheus.Registry()
        content, http_headers = aioprometheus.render(registry, accepts_headers)
        self.assertEqual(
            http_headers["Content-Type"], aioprometheus.formats.BINARY_CONTENT_TYPE
        )
