import base64

# imports only used for type annotations
from urllib.parse import quote_plus, urljoin

try:
    import aiohttp
except ImportError as exc:
    raise ImportError(
        "`aiohttp` could not be imported. Did you install `aioprometheus` "
        "with the `aiohttp` extra?"
    ) from exc

from aioprometheus import REGISTRY, Registry
from aioprometheus.formats import text


class Pusher:
    """
    This class can be used in applications that can't support the
    standard pull strategy. The pusher object pushes the metrics
    to a push-gateway which can be scraped by Prometheus.
    """

    PROMETHEUS_PATH = "/metrics"

    def __init__(
        self,
        job_name: str,
        addr: str,
        grouping_key: dict = None,
        path: str = "/metrics",
    ) -> None:
        """

        :param job_name: The name of the job.

        :param addr: The address of the push gateway. The default port the
          push gateway listens on is 9091 so the address will typically be
          something like this ``http://hostname:9091``.

        :param grouping_key: Specifies the grouping key of created metrics
          in key-value pairs.

        :param loop: The event loop instance to use. If no loop is specified
          then the default event loop will be used.

        :param path: The path to use, by default this will be /metrics for
           prometheus but can be optionally specified to work with other
           platforms such as VictoriaMetrics.
        """
        self.job_name = job_name

        if grouping_key is None:
            grouping_key = {}
        self.grouping_key = grouping_key

        self.addr = addr
        self.formatter = text.TextFormatter()
        self.headers = self.formatter.get_headers()

        if path == self.PROMETHEUS_PATH:
            path = path + "".join(
                _escape_grouping_key(str(k), str(v))
                for k, v in [("job", job_name)] + sorted(grouping_key.items())
            )

        self.path = urljoin(self.addr, path)

    async def add(self, registry: Registry = REGISTRY) -> "aiohttp.ClientResponse":
        """
        ``add`` works like replace, but only metrics with the same name as the
        newly pushed metrics are replaced.
        """
        async with aiohttp.ClientSession() as session:
            payload = self.formatter.marshall(registry)
            async with session.post(
                self.path, data=payload, headers=self.headers
            ) as resp:
                return resp

    async def replace(self, registry: Registry = REGISTRY) -> "aiohttp.ClientResponse":
        """
        ``replace`` pushes new values for a group of metrics to the push
        gateway.

        .. note::

            All existing metrics with the same grouping key specified in the
            URL will be replaced with the new metrics value.

        """
        async with aiohttp.ClientSession() as session:
            payload = self.formatter.marshall(registry)
            async with session.put(
                self.path, data=payload, headers=self.headers
            ) as resp:
                return resp

    async def delete(self, registry: Registry = REGISTRY) -> "aiohttp.ClientResponse":
        """
        ``delete`` deletes metrics from the push gateway. All metrics with
        the grouping key specified in the URL are deleted.
        """
        async with aiohttp.ClientSession() as session:
            payload = self.formatter.marshall(registry)
            async with session.delete(
                self.path, data=payload, headers=self.headers
            ) as resp:
                return resp


def _escape_grouping_key(k, v):
    if v == "":
        # To encode the empty label with base64, you have to use at least one
        # `=` padding character to avoid a `//` or a trailing `/`.
        grouping_key = f"/{k}@base64/="
    elif "/" in v:
        # The plain (or even URI-encoded) `/` would otherwise be interpreted as
        # a path separator.
        v = base64.urlsafe_b64encode(v.encode("utf-8")).decode()
        grouping_key = f"/{k}@base64/{v}"
    else:
        v = quote_plus(v)
        grouping_key = f"/{k}/{v}"

    return grouping_key
