import unittest

from aioprometheus.collectors import REGISTRY
from aioprometheus.collector.platform import CollectorPlatform


class TestCollectorPlatfrom(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        REGISTRY.clear()

    def setUp(self) -> None:
        self.COLLECTOR_PLATFORM = CollectorPlatform()

    def tearDown(self):
        REGISTRY.clear()

    def test_python_info_is_present(self):
        REGISTRY.get(self.COLLECTOR_PLATFORM.name)
        self.assertIn("python_info", REGISTRY.collectors)

    def test_get(self):
        labels = self.COLLECTOR_PLATFORM._labels()
        self.assertEqual(self.COLLECTOR_PLATFORM.get(labels), 1)
