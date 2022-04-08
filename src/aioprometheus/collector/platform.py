# metrics as reported by client_python 
## HELP python_info Python platform information
## TYPE python_info gauge
# python_info{implementation="CPython",major="3",minor="10",patchlevel="5",version="3.10.5"} 1.0

import typing as t

import sys

import aioprometheus.collectors


class CollectorPlatform(aioprometheus.collectors.Gauge):
    """Collector for python platform information"""

    def __init__(
        self,
        registry: aioprometheus.collectors.Registry = None,
    ):
        super().__init__(
            "python_info", "Python platform information", registry=registry
        )
        labels = self._labels()
        self.set_value(labels, 1)

    def _labels(self) -> t.Dict[str, str]:
        return {
            "version": sys.version,
            "implementation": sys.implementation.name,
            "major": str(sys.version_info.major),
            "minor": str(sys.version_info.minor),
            "patchlevel": str(sys.version_info.micro),
            "system": sys.platform,
        }


COLLECTOR_PLATFORM = CollectorPlatform()
