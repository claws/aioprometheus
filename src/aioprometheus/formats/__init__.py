from .base import IFormatter
from . import text

try:
    from . import binary
except ImportError:
    binary = None
