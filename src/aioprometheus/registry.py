from typing import Dict, List, Union

from .collectors import Collector, Counter, Gauge, Histogram, Summary

CollectorsType = Union[Counter, Gauge, Histogram, Summary]


class CollectorRegistry:
    """This class implements the metrics collector registry.

    Collectors in the registry must comply with the Collector interface
    which means that they inherit from the base Collector object and implement
    a no-argument method called 'get_all' that returns a list of Metric
    instance objects.
    """

    def __init__(self) -> None:
        self.collectors = {}  # type: Dict[str, CollectorsType]

    def register(self, collector: CollectorsType) -> None:
        """Register a collector.

        This will allow the collector metrics to be emitted.

        :param collector: A collector to register in the registry.

        :raises: TypeError if collector is not an instance of
          :class:`Collector`.

        :raises: ValueError if collector is already registered.
        """
        if not isinstance(collector, Collector):
            raise TypeError(f"Invalid collector type: {collector}")

        if collector.name in self.collectors:
            raise ValueError(f"Collector {collector.name} is already registered")

        self.collectors[collector.name] = collector

    def deregister(self, name: str) -> None:
        """Deregister a collector.

        This will stop the collector metrics from being emitted.

        :param name: The name of the collector to deregister.

        :raises: KeyError if collector is not already registered.
        """
        del self.collectors[name]

    def get(self, name: str) -> CollectorsType:
        """Get a collector by name.

        :param name: The name of the collector to fetch.

        :raises: KeyError if collector is not found.
        """
        return self.collectors[name]

    def get_all(self) -> List[CollectorsType]:
        """Return a list of all collectors"""
        return list(self.collectors.values())


# The default registry.
Registry = CollectorRegistry
