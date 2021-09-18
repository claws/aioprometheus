import unittest

from aioprometheus.histogram import (
    POS_INF,
    Histogram,
    exponentialBuckets,
    linearBuckets,
)


class TestHistogram(unittest.TestCase):
    """Test histogram module"""

    def test_histogram(self):

        with self.assertRaises(Exception) as context:
            h = Histogram()
        self.assertEqual("Must have at least two buckets", str(context.exception))

        with self.assertRaises(Exception) as context:
            h = Histogram(10.0, 5.0)
        self.assertEqual("Buckets not in sorted order", str(context.exception))

        buckets = (5.0, 10.0, 15.0)
        expected_keys = (5.0, 10.0, 15.0, POS_INF)
        h = Histogram(*buckets)
        self.assertEqual(tuple(h.buckets.keys()), expected_keys)
        inputs = (
            (3, (1, 1, 1, 1)),
            (5.2, (1, 2, 2, 2)),
            (13, (1, 2, 3, 3)),
            (4, (2, 3, 4, 4)),
        )
        test_sum = 0
        for test_count, (value, expected_values) in enumerate(inputs, start=1):
            h.observe(value)
            test_sum += value
            self.assertEqual(h.observations, test_count)
            self.assertEqual(h.sum, test_sum)
            self.assertEqual(tuple(h.buckets.values()), expected_values)

    def test_linear_bucket_helper_functions(self):

        buckets = linearBuckets(1, 2, 5)
        self.assertEqual(buckets, [1, 3, 5, 7, 9])

        h = Histogram(*buckets)

        with self.assertRaises(Exception) as context:
            buckets = linearBuckets(1, 2, 0)
        self.assertEqual(
            "Invalid count, must be a positive number", str(context.exception)
        )

    def test_exponential_bucket_helper_functions(self):

        buckets = exponentialBuckets(1, 10, 5)
        self.assertEqual(buckets, [1, 10, 100, 1000, 10000])
        h = Histogram(*buckets)

        with self.assertRaises(Exception) as context:
            buckets = exponentialBuckets(1, 10, 0)
        self.assertEqual(
            "Invalid count, must be a positive number", str(context.exception)
        )

        with self.assertRaises(Exception) as context:
            buckets = exponentialBuckets(-1, 10, 3)
        self.assertEqual("Invalid start, must be positive", str(context.exception))

        with self.assertRaises(Exception) as context:
            buckets = exponentialBuckets(1, 0.5, 10)
        self.assertEqual(
            "Invalid factor, must be greater than one", str(context.exception)
        )
