'''
This module implements an asynchronous Prometheus.io metrics service.
The service is built upon ``aiohttp``.
'''

import asyncio
import logging

import aiohttp
import aiohttp.web

from aiohttp.hdrs import (
    METH_GET as GET,
    ACCEPT)

from .negotiator import negotiate
from .registry import Registry
from typing import Set

# imports only used for type annotations
from asyncio.base_events import BaseEventLoop, Server
from ssl import SSLContext


logger = logging.getLogger(__name__)

DEFAULT_METRICS_PATH = '/metrics'


class Service(object):
    '''
    This class implements a Prometheus.io metrics service that can
    be embedded within asyncio based applications so they can be scraped
    by the Prometheus.io server.
    '''

    def __init__(self,
                 registry: Registry = None,
                 loop: BaseEventLoop = None) -> None:
        '''
        Initialise the Prometheus metrics service.

        :param registry: A :class:`CollectorRegistry` instance that will
          hold all the metrics for this service. If no registry if specified
          then the default registry is used.

        :param loop: The event loop instance to use. If no loop is specified
          then the default event loop will be retrieved.

        :raises: Exception if the registry object is not an instance of the
          Registry type.
        '''
        self.loop = loop or asyncio.get_event_loop()
        if registry is not None and not isinstance(registry, Registry):
            raise Exception(
                'registry must be a Registry, got: {}'.format(registry))
        self.registry = registry or Registry()
        self._svr = None  # type: Server
        self._svc = None  # type: aiohttp.web.Application
        self._handler = None  # type: aiohttp.web.RequestHandlerFactory
        self._https = None  # type: bool

    @property
    def url(self) -> str:
        ''' Return the Prometheus metrics url

        :raises: Exception if the server has not been started.

        :return: the service URL as a string
        '''
        if self._svr is None:
            raise Exception(
                "No URL available, Prometheus metrics server is not running")

        # IPv4 returns 2-tuple, IPv6 returns 4-tuple
        host, port, *_ = self._svr.sockets[0].getsockname()
        scheme = "http{}".format('s' if self._https else '')
        url = "{scheme}://{host}:{port}{metrics_url}".format(
            scheme=scheme,
            host=host if ":" not in host else "[{}]".format(host),
            port=port,
            metrics_url=self._metrics_url)
        return url

    async def start(self,
                    addr: str = '',
                    port: int = 0,
                    ssl: SSLContext = None,
                    metrics_url: str = DEFAULT_METRICS_PATH,
                    discovery_agent=None) -> None:
        ''' Start the prometheus metrics HTTP(S) server.

        :param addr: the address to bind the server on. By default this is
          set to an empty string so that the service becomes available on
          all interfaces.

        :param port: The port to bind the server on. The default value is 0
          which will cause the server to bind to an ephemeral port. If you
          want the server to operate on a fixed port then you need to specifiy
          the port.

        :param ssl: a sslContext for use with TLS.

        :param metrics_url: The name of the endpoint route to expose
          prometheus metrics on. Defaults to '/metrics'.

        :param discovery_agent: an agent that can register the metrics
          service with a service discovery mechanism.

        :raises: Exception if the server could not be started.
        '''
        logger.debug(
            'Prometheus metrics server starting on %s:%s%s',
            addr, port, metrics_url)

        if self._svr:
            logger.warning(
                'Prometheus metrics server is already running')
            return

        self._svc = aiohttp.web.Application()
        self._metrics_url = metrics_url
        self._svc.router.add_route(
            GET, metrics_url, self.handle_metrics)
        self._handler = self._svc.make_handler()
        self._https = ssl is not None
        try:
            self._svr = await self.loop.create_server(
                self._handler, addr, port, ssl=ssl)
        except Exception:
            logger.exception('error creating metrics server')
            raise

        logger.debug('Prometheus metrics server started on %s', self.url)

        # register service with service discovery
        if discovery_agent:
            await discovery_agent.register(self)

    async def stop(self,
                   wait_duration: float = 1.0,
                   discovery_agent=None) -> None:
        ''' Stop the prometheus metrics HTTP(S) server.

        :param wait_duration: the number of seconds to wait for connections to
          finish.

        :param discovery_agent: an agent that can register the metrics
          service with a service discovery mechanism.

        '''
        logger.debug(
            'Prometheus metrics server stopping')

        if self._svr is None:
            logger.warning(
                'Metrics HTTP Server is already stopped')
            return

        # de-register service with service discovery
        if discovery_agent:
            await discovery_agent.deregister(self)

        self._svr.close()
        await self._svr.wait_closed()
        await self._svc.shutdown()
        await self._handler.finish_connections(wait_duration)
        await self._svc.cleanup()
        self._svr = None
        self._svc = None
        self._handler = None
        logger.debug('Prometheus metrics server stopped')

    async def handle_metrics(self,
                             request: aiohttp.web.Request) -> aiohttp.web.Response:
        ''' Handle a request to the metrics route.

        The request is inspected and the most efficient response data format
        is chosen.
        '''
        Formatter = negotiate(self.accepts(request))
        formatter = Formatter(False)

        resp = aiohttp.web.Response()
        resp.headers.update(formatter.get_headers())
        resp.body = formatter.marshall(self.registry)
        return resp

    def accepts(self,
                request: aiohttp.web.Request) -> Set[str]:
        ''' Return a sequence of accepts items in the request headers '''
        accepts = set()  # type: Set[str]
        accept_headers = request.headers.getall(ACCEPT)
        logger.debug('accept: {}'.format(accept_headers))
        for accept_items in accept_headers:
            if ';' in accept_items:
                accept_items = [i.strip() for i in accept_items.split(';')]
            else:
                accept_items = [accept_items]
            accepts.update(accept_items)
        return accepts
