'''
This module implements part of a custom service discovery approach that uses
``etcd``, a highly consistent distributed key-value store, to store the
metrics service information. This information can be retrieved (using a
separate ``etcd`` reader tool) and made available to the Prometheus server.

Application's instrumented with the ``aioprometheus`` metrics service expose
an endpoint for the Prometheus Server to scrape metrics from. The
``EtcdAgent`` in this module is used by an application to register (and
deregister) its metrics service (i.e. ``/metrics``) endpoint with the
service discovery store (i.e. etcd) using a pre-defined key schema:

.. code-block:: console

    /services/<service_name> = <service_data>

The data contained in the ``service_data`` value is a dict of information
associated with the service:

.. code-block:: json

    {
     "service_name": "service_a",
     "tags": [("hostname", "hostname_a")],
     "address": "http://<addr>:<port>/metrics"
    }

'''

import asyncio
import json
import logging

from aio_etcd.client import Client as EtcdClient
from .agent import IDiscoveryAgent

# imports only used for type annotations
from asyncio.base_events import BaseEventLoop
from ..service import Service


logger = logging.getLogger(__name__)


class EtcdAgent(IDiscoveryAgent):
    '''
    This class implements a service discovery mechansim that allows an
    Prometheus service to register itself with a service discovery tool
    so that Prometheus can discover new applications to monitor. This
    implementation uses etcd as the backing store for service discovery.

    This mechanism stores key values as JSON objects.
    '''

    def __init__(self,
                 service_name: str,
                 tags=(),
                 loop: BaseEventLoop = None,
                 **kwargs) -> None:
        '''

        :param service_name: a string that uniquely defines the service
          name. This name will be used to register the Prometheus metrics
          service for an application in to etcd. The responsibility for
          coming up with unique service names is outside the scope of this
          client.

        :param tags: a optional sequence of key-value tuples.

        :keywords: are passed straight down to the etcd client.
        '''
        self.service_name = service_name
        self.tags = tags
        self.loop = loop or asyncio.get_event_loop()
        self.client = EtcdClient(loop=self.loop, **kwargs)

    async def register(self, metrics_server: Service) -> None:
        '''
        Register a Prometheus metrics server with etcd.

        :param metrics_server: an instance of a :class:`Service`

        :param loop: an event loop instance. If no event loop is provided
          then the default event will be used.
        '''
        key = '/services/{}'.format(self.service_name)
        value = dict(
            service_name=self.service_name,
            tags=self.tags,
            address=metrics_server.url)
        await self.client.write(key, json.dumps(value))

    async def deregister(self, metrics_server: Service) -> None:
        '''
        Register a Prometheus metrics server from etcd.

        :param metrics_server: an instance of a :class:`MetricsServer`

        :param loop: an event loop instance. If no event loop is provided
          then the default event will be used.
        '''
        key = '/services/{}'.format(self.service_name)
        await self.client.delete(key)

    async def close(self) -> None:
        '''
        Stop the agent. This method does not deregister the service.
        '''
        if self.client:
            self.client.close()
