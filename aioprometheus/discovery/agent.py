'''
This module implements the abstract service discovery API interface.
'''

import abc


class IDiscoveryAgent(abc.ABC):
    '''
    This class represents the abstract base class for a discovery agent.
    '''

    async def register(self, metrics_server):
        '''
        Register a Prometheus metrics server with service discovery.

        :param metrics_server: an instance of a :class:`MetricsServer`
        '''
        raise NotImplementedError

    async def deregister(self, metrics_server):
        '''
        Register a Prometheus metrics server from service discovery.

        :param metrics_server: an instance of a :class:`MetricsServer`
        '''
        raise NotImplementedError
