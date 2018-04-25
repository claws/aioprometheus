
import logging

from . import formats
from typing import Callable, Set


logger = logging.getLogger(__name__)

# type aliases
FormatterType = Callable[[bool], formats.IFormatter]


ProtobufAccepts = set(formats.BINARY_CONTENT_TYPE.split('; '))
TextAccepts = set(formats.TEXT_CONTENT_TYPE.split('; '))


def negotiate(accepts: Set[str]) -> FormatterType:
    ''' Negotiate a response format by scanning through the ACCEPTS
    header and selecting the most efficient format.

    The formatter returned by this function is used to render a response.

    :param accepts: a set of ACCEPT headers fields extracted from a request.

    :returns: a formatter class to form up the response into the
      appropriate representation.
    '''
    if not isinstance(accepts, set):
        raise TypeError(
            'Expected a set but got {}'.format(type(accepts)))

    formatter = formats.TextFormatter  # type: FormatterType

    if ProtobufAccepts.issubset(accepts):
        formatter = formats.BinaryFormatter  # type: ignore

    logger.debug(
        'negotiating %s resulted in choosing %s',
        accepts, formatter.__name__)

    return formatter
