
import asyncio
import json
import logging

from aio_etcd.client import Client as EtcdClient
from .agent import IDiscoveryAgent


logger = logging.getLogger(__name__)


class EtcdAgent(IDiscoveryAgent):
    '''
    This class implements a service discovery mechansim that allows an
    Prometheus service to register itself with a service discovery tool
    so that Prometheus can discover new applications to monitor. This
    implementation uses etcd as the backing store for service discovery.

    This mechanism stores key values as JSON objects.
    '''

    def __init__(self, service_name, tags=(), loop=None, **kwargs):
        '''

        :param service_name: a string that uniquely defines the service
          name. This name will be used to register the Prometheus metrics
          service for an application in to etcd. The responsibility for
          coming up with unique service names is outside the scope of this
          client.

        :keywords: are passed straight down to the etcd client.
        '''
        self.service_name = service_name
        self.tags = tags
        self.loop = loop or asyncio.get_event_loop()
        self.client = EtcdClient(loop=self.loop, **kwargs)

    async def register(self, metrics_server):
        '''
        Register a Prometheus metrics server with etcd.

        :param metrics_server: an instance of a :class:`Service`

        :param loop: an event loop instance. If no event loop is provided
          then the default event will be used.
        '''
        key = '/metrics/{}'.format(self.service_name)
        value = dict(
            service_name=self.service_name,
            tags=self.tags,
            url=metrics_server.url)
        await self.write(key, json.dumps(value))

    async def deregister(self, metrics_server):
        '''
        Register a Prometheus metrics server from etcd.

        :param metrics_server: an instance of a :class:`MetricsServer`

        :param loop: an event loop instance. If no event loop is provided
          then the default event will be used.
        '''
        key = '/metrics/{}'.format(self.service_name)
        await self.delete(key)

    async def close(self):
        '''
        Stop the agent. This method does not deregister the service.
        '''
        if self.client:
            self.client.close()
