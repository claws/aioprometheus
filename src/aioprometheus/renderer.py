from typing import Sequence, Tuple, Union

from .formats import IFormatter
from .negotiator import negotiate
from .registry import Registry


def render(registry: Registry, accepts_headers: Sequence[str]) -> Tuple[bytes, dict]:
    """Render the metrics in this registry to a specific format.

    The format chosen is determined by scanning through the ACCEPTS headers
    and selecting the most efficient format. If no accepts headers
    information is provided then Text format is used as the default.

    :param registry: A collector registry that contains the metrics to be
      rendered into a specific format.

    :param accepts_headers: a list of ACCEPT headers fields extracted from a request.

    :returns: a 2-tuple where the first item is a bytes object that
        represents the formatted metrics and the second item is a dict of
        header fields that can be added to a HTTP response.
    """
    if not isinstance(registry, Registry):
        raise Exception(f"registry must be a Registry, got: {type(registry)}")

    if not isinstance(accepts_headers, (set, list, tuple)):
        raise Exception(
            f"accepts_headers must be a sequence, got: {type(accepts_headers)}"
        )

    Formatter = negotiate(accepts_headers)
    formatter = Formatter()  # type: IFormatter

    http_headers = formatter.get_headers()
    content = formatter.marshall(registry)
    return content, http_headers
