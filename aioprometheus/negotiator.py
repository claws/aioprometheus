
import logging

from .formats import BinaryFormatter, TextFormatter
from typing import Callable, Set, Union

logger = logging.getLogger(__name__)

# type aliases
BinaryFormatterClass = Callable[[bool], BinaryFormatter]
TextFormatterClass = Callable[[bool], TextFormatter]
FormatterType = Union[BinaryFormatterClass, TextFormatterClass]


ProtobufAccepts = set(
    ['application/vnd.google.protobuf',
     'proto=io.prometheus.client.MetricFamily',
     'encoding=delimited'])

TextAccepts = set(['text/plain', 'version=0.0.4'])


def negotiate(accepts: Set[str]) -> FormatterType:
    ''' Negotiate a response format by scanning through the ACCEPTS
    header and selecting the most efficient format.

    :param accepts: a set of ACCEPT headers fields extracted from a request.

    :returns: a formatter class that should be used to form up the
      response into the appropriate representation.
    '''
    if not isinstance(accepts, set):
        raise TypeError(
            'Expected a set but got {}'.format(type(accepts)))

    formatter = TextFormatter  # type: FormatterType

    if ProtobufAccepts.issubset(accepts):
        formatter = BinaryFormatter
    elif TextAccepts.issubset(accepts):
        formatter = TextFormatter

    logger.debug(
        'negotiating {} resulted in choosing {}'.format(
            accepts, formatter.__name__))
    return formatter
