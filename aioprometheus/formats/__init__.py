
import importlib.util
from .base import IFormatter
from .text import TextFormatter

binary_format_spec = importlib.util.find_spec("aioprometheus_binary_format")
binary_format_available = binary_format_spec is not None
if binary_format_available:
    from aioprometheus_binary_format import BinaryFormatter
