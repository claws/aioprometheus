""" This sub-package implements metrics formatters """
from . import text

try:
    from . import binary
except ImportError:
    binary = None  # type: ignore
