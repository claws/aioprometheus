import logging
from typing import Sequence, Set, Type

from . import formats

logger = logging.getLogger(__name__)

# type aliases
FormatterType = Type[formats.IFormatter]


def negotiate(accepts_headers: Sequence[str]) -> FormatterType:
    """Negotiate a response format by scanning through a list of ACCEPTS
    headers and selecting the most efficient format.

    The formatter returned by this function is used to render a response.

    :param accepts_headers: a list of ACCEPT headers fields extracted from a request.

    :returns: a formatter class to form up the response into the
      appropriate representation.
    """
    accepts = parse_accepts(accepts_headers)

    formatter = formats.text.TextFormatter  # type: FormatterType

    if formats.binary is not None:
        if formats.binary.BINARY_ACCEPTS.issubset(accepts):
            formatter = formats.binary.BinaryFormatter  # type: ignore

    logger.debug(f"negotiating {accepts} resulted in choosing {formatter.__name__}")

    return formatter


def parse_accepts(accept_headers: Sequence[str]) -> Set[str]:
    """Return a sequence of accepts items in the request headers"""
    accepts = set()  # type: Set[str]
    for accept_header in accept_headers:
        if ";" in accept_header:
            accept_items = [i.strip() for i in accept_header.split(";")]
        else:
            accept_items = [accept_header]
        accepts.update(accept_items)
    return accepts
