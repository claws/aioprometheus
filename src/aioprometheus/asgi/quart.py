from quart import current_app, request

from aioprometheus import REGISTRY, render


async def metrics():
    """Render metrics into format specified by 'accept' header.

    This function first attempts to retrieve the metrics Registry from
    ``current_app`` in case the app is using a custom registry instead
    of the default registry. If this fails then the default registry is used.
    """
    registry = current_app.registry if hasattr(current_app, "registry") else REGISTRY
    content, http_headers = render(registry, request.headers.getlist("accept"))
    return content, http_headers
