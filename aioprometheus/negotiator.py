
import logging

from . import formats
from typing import Callable, Set


logger = logging.getLogger(__name__)

# type aliases
FormatterType = Callable[[bool], formats.IFormatter]


ProtobufAccepts = set(
    ['application/vnd.google.protobuf',
     'proto=io.prometheus.client.MetricFamily',
     'encoding=delimited'])

TextAccepts = set(['text/plain', 'version=0.0.4'])


def negotiate(accepts: Set[str]) -> FormatterType:
    ''' Negotiate a response format by scanning through the ACCEPTS
    header and selecting the most efficient format.

    :param accepts: a set of ACCEPT headers fields extracted from a request.

    :returns: a formatter class to form up the response into the
      appropriate representation.
    '''
    if not isinstance(accepts, set):
        raise TypeError(
            'Expected a set but got {}'.format(type(accepts)))

    formatter = formats.TextFormatter  # type: FormatterType

    if ProtobufAccepts.issubset(accepts):
        if formats.binary_format_available:
            formatter = formats.BinaryFormatter  # type: ignore
        else:
            logger.warning(
                'No binary formatter available, falling back to text format')

    logger.debug(
        'negotiating %s resulted in choosing %s',
        accepts, formatter.__name__)
    return formatter
