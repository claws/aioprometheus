import unittest

from aioprometheus.formats import binary, text
from aioprometheus.negotiator import negotiate


class TestNegotiate(unittest.TestCase):
    def test_protobuffer(self):
        """ check that a protobuf formatter is returned """
        headers = (
            "proto=io.prometheus.client.MetricFamily;application/vnd.google.protobuf;encoding=delimited",
            "application/vnd.google.protobuf;proto=io.prometheus.client.MetricFamily;encoding=delimited",
            "encoding=delimited;application/vnd.google.protobuf;proto=io.prometheus.client.MetricFamily",
        )

        for accept in headers:
            self.assertEqual(binary.BinaryFormatter, negotiate(set(accept.split(";"))))

    def test_text_004(self):
        """ check that a text formatter is returned for version 0.0.4 """
        headers = (
            "text/plain; version=0.0.4",
            "text/plain;version=0.0.4",
            "version=0.0.4; text/plain",
        )

        for accept in headers:
            self.assertEqual(text.TextFormatter, negotiate(set(accept.split(";"))))

    def test_text_default(self):
        """ check that a text formatter is returned for plain text """
        headers = ("text/plain;",)

        for accept in headers:
            self.assertEqual(text.TextFormatter, negotiate(set(accept.split(";"))))

    def test_default(self):
        """ check that a text formatter is returned if no matches """
        headers = ("application/json", "*/*", "application/nothing")

        for accept in headers:
            self.assertEqual(text.TextFormatter, negotiate(set(accept.split(";"))))

    def test_no_accept_header(self):
        """ check request with no accept header works """
        self.assertEqual(text.TextFormatter, negotiate(set()))
        self.assertEqual(text.TextFormatter, negotiate(set([""])))
