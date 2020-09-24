from . import text
from .base import IFormatter

try:
    from . import binary
except ImportError:
    binary = None
