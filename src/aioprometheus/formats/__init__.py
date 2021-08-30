""" This sub-package implements metrics formatters """
from . import text
from .base import IFormatter

try:
    from . import binary
except ImportError:
    binary = None  # type: ignore
