
from .collectors import Collector


class CollectorRegistry(object):
    ''' This class implements the metrics collector registry.

    Collectors must comply with the ICollector interface which means that they
    have a no-argument method called 'collect' that returns a list of Metric
    objects. These objects should be consistent with the Prometheus exposition
    formats.
    '''

    def __init__(self):
        self.collectors = {}

    def register(self, collector):
        ''' Register a collector

        :raises: TypeError if collector is not an instance of
          :class:`Collector`.
        :raises: ValueError if collector is already registered.
        '''
        if not isinstance(collector, Collector):
            raise TypeError(
                'Invalid collector type. Expected Collector. got {}'.format(
                    type(collector)))

        if collector.name in self.collectors:
            raise ValueError(
                "Collector {} is already registered".format(
                    collector.name))

        self.collectors[collector.name] = collector

    def deregister(self, name):
        ''' Deregister a collector '''
        del self.collectors[name]

    def get(self, name):
        ''' Get a collector

        :raises: KeyError if collector is not found.
        '''
        return self.collectors[name]

    def get_all(self):
        ''' Return a list of all collectors '''
        return list(self.collectors.values())

    # def collect(self):
    #     ''' This generator yields metrics from the collectors in the registry '''
    #     for collector in self.collectors:
    #         for metric in collector.collect():
    #             yield metric


# The default registry.
Registry = CollectorRegistry
