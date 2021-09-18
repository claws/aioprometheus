"""
This module implements an asynchronous Prometheus metrics export service.
"""

import logging

try:
    import aiohttp
except ImportError as exc:
    raise ImportError(
        "`aiohttp` could not be imported. Did you install `aioprometheus` "
        "with the `aiohttp` extra?"
    ) from exc
# imports only used for type annotations
from ssl import SSLContext
from typing import Optional

import aiohttp.web
from aiohttp.hdrs import ACCEPT
from aiohttp.hdrs import METH_GET as GET

from aioprometheus import REGISTRY, Registry, render

logger = logging.getLogger(__name__)

DEFAULT_METRICS_PATH = "/metrics"


class Service:
    """
    This class implements a Prometheus metrics service that can
    be embedded within asyncio based applications so they can be scraped
    by the Prometheus.io server.
    """

    def __init__(self, registry: Registry = REGISTRY) -> None:
        """
        Initialise the Prometheus metrics service.

        :param registry: The :class:`Registry` instance that holds all the
          metrics that this service should expose. If no registry is specified
          then the default registry will be used.

        :raises: Exception if the registry object passed is not an instance of
          the Registry type.
        """
        if not isinstance(registry, Registry):
            raise Exception(f"registry must be a Registry, got: {registry}")
        self.registry = registry
        self._site = None  # type: Optional[aiohttp.web.TCPSite]
        self._app = None  # type: Optional[aiohttp.web.Application]
        self._runner = None  # type: Optional[aiohttp.web.AppRunner]
        self._https = False
        self._root_url = "/"
        self._metrics_url = None  # type: Optional[str]

    @property
    def base_url(self) -> str:
        """Return the base service url

        :raises: Exception if the server has not been started.

        :return: the base service URL as a string
        """
        if self._site is None:
            raise Exception(
                "No URL available, Prometheus metrics server is not running"
            )

        # Keep mypy happy by checking runner is not None.
        if self._runner is None:
            raise Exception(
                "No URL available, Prometheus metrics server is not running"
            )

        # IPv4 address returns a 2-tuple, IPv6 returns a 4-tuple
        host, port, *_ = self._runner.addresses[0]
        scheme = f"http{'s' if self._https else ''}"
        host = host if ":" not in host else f"[{host}]"
        url = f"{scheme}://{host}:{port}"
        return url

    @property
    def root_url(self) -> str:
        """Return the root service url

        :raises: Exception if the server has not been started.

        :return: the root URL as a string
        """
        return f"{self.base_url}{self._root_url}"

    @property
    def metrics_url(self) -> str:
        """Return the Prometheus metrics url

        :raises: Exception if the server has not been started.

        :return: the metrics URL as a string
        """
        return f"{self.base_url}{self._metrics_url}"

    async def start(
        self,
        addr: str = "",
        port: int = 0,
        ssl: SSLContext = None,
        metrics_url: str = DEFAULT_METRICS_PATH,
    ) -> None:
        """Start the prometheus metrics HTTP(S) server.

        :param addr: the address to bind the server on. By default this is
          set to an empty string so that the service becomes available on
          all interfaces.

        :param port: The port to bind the server on. The default value is 0
          which will cause the server to bind to an ephemeral port. If you
          want the server to operate on a fixed port then you need to specify
          the port.

        :param ssl: a sslContext for use with TLS.

        :param metrics_url: The name of the endpoint route to expose
          prometheus metrics on. Defaults to '/metrics'.

        :raises: Exception if the server could not be started.
        """
        logger.debug(
            f"Prometheus metrics server starting on {addr}:{port}{metrics_url}"
        )

        if self._site:
            logger.warning("Prometheus metrics server is already running")
            return

        self._app = aiohttp.web.Application()
        self._metrics_url = metrics_url
        self._app["metrics_url"] = metrics_url
        self._app.router.add_route(GET, metrics_url, self.handle_metrics)
        self._app.router.add_route(GET, self._root_url, self.handle_root)
        self._app.router.add_route(GET, "/robots.txt", self.handle_robots)
        self._runner = aiohttp.web.AppRunner(self._app)
        await self._runner.setup()

        self._https = ssl is not None
        try:
            self._site = aiohttp.web.TCPSite(
                self._runner, addr, port, ssl_context=ssl, shutdown_timeout=2.0
            )
            await self._site.start()
        except Exception:
            logger.exception("error creating metrics server")
            raise

        logger.debug(f"Prometheus metrics server started on {self.metrics_url}")

    async def stop(self) -> None:
        """Stop the prometheus metrics HTTP(S) server"""
        logger.debug("Prometheus metrics server stopping")

        if self._site is None:
            logger.warning("Prometheus metrics server is already stopped")
            return

        # Keep mypy happy by checking runner is not None.
        if self._runner is None:
            raise Exception("Prometheus metrics server is not running")

        await self._runner.cleanup()
        self._site = None
        self._app = None
        self._runner = None
        logger.debug("Prometheus metrics server stopped")

    async def handle_metrics(
        self, request: "aiohttp.web.Request"
    ) -> "aiohttp.web.Response":
        """Handle a request to the metrics route.

        The request is inspected and the most efficient response data format
        is chosen.
        """
        content, http_headers = render(
            self.registry, request.headers.getall(ACCEPT, [])
        )
        return aiohttp.web.Response(body=content, headers=http_headers)

    async def handle_root(
        self, request: "aiohttp.web.Request"
    ) -> "aiohttp.web.Response":
        """Handle a request to the / route.

        Serves a trivial page with a link to the metrics.  Use this if ever
        you need to point a health check at your the service.
        """
        metrics_url = request.app["metrics_url"]
        return aiohttp.web.Response(
            content_type="text/html",
            text=f"<html><body><a href='{metrics_url}'>metrics</a></body></html>",
        )

    async def handle_robots(
        self,
        request: "aiohttp.web.Request",  # pylint: disable=unused-argument
    ) -> "aiohttp.web.Response":
        """Handle a request to /robots.txt

        If a robot ever stumbles on this server, discourage it from indexing.
        """
        return aiohttp.web.Response(
            content_type="text/plain", text="User-agent: *\nDisallow: /\n"
        )
