from starlette.requests import Request
from starlette.responses import Response

from aioprometheus import REGISTRY, render


async def metrics(request: Request) -> Response:
    """Render metrics into format specified by 'accept' header.

    This function first attempts to retrieve the metrics Registry from
    ``request.app.state`` in case the app is using a custom registry instead
    of the default registry. If this fails then the default registry is used.
    """
    registry = (
        request.app.state.registry
        if hasattr(request.app.state, "registry")
        else REGISTRY
    )
    content, http_headers = render(registry, request.headers.getlist("Accept"))
    return Response(content=content, media_type=http_headers["Content-Type"])
