
import importlib.util
from .base import IFormatter
from .text import TextFormatter

prometheus_metrics_proto_lib = importlib.util.find_spec("prometheus_metrics_proto")
binary_format_available = prometheus_metrics_proto_lib is not None
if binary_format_available:
    from .binary import BinaryFormatter
