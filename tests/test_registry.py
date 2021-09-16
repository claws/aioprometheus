import unittest

from aioprometheus import REGISTRY, Counter, Gauge, Registry, Summary
from aioprometheus.collectors import Collector


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.data = {
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {"app": "my_app"},
        }

    def tearDown(self):
        REGISTRY.clear()

    def test_register_same_names(self):
        """check registering same metrics raises exception"""
        c1 = Collector(**self.data)

        with self.assertRaises(ValueError) as context:
            c2 = Collector(**self.data)

        collector_name = self.data["name"]
        self.assertEqual(
            f"A collector for {collector_name} is already registered",
            str(context.exception),
        )

    def test_register_wrong_type(self):
        """check registering an invalid collector raises an exception"""
        with self.assertRaises(TypeError) as context:
            REGISTRY.register("This should fail")
        self.assertIn("Invalid collector type: ", str(context.exception))

    def test_deregister(self):
        """check collectors can be deregistered"""
        c = Collector(**self.data)
        REGISTRY.deregister(self.data["name"])
        self.assertEqual(0, len(REGISTRY.collectors))

    def test_get(self):
        c = Collector(**self.data)
        self.assertEqual(c, REGISTRY.get(c.name))

    def test_get_all(self):
        q = 100
        collectors = [Collector("test" + str(i), "Test" + str(i)) for i in range(q)]
        result = REGISTRY.get_all()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(q, len(result))
