import unittest

from aioprometheus.formats import text
from aioprometheus.negotiator import negotiate


class TestNegotiate(unittest.TestCase):
    def test_text_default(self):
        """check that a text formatter is returned for plain text"""
        headers = ("text/plain;",)

        for accept in headers:
            self.assertEqual(text.TextFormatter, negotiate(set(accept.split(";"))))

    def test_default(self):
        """check that a text formatter is returned if no matches"""
        headers = ("application/json", "*/*", "application/nothing")

        for accept in headers:
            self.assertEqual(text.TextFormatter, negotiate(set(accept.split(";"))))

    def test_text_004(self):
        """check that a text formatter is returned for version 0.0.4"""
        headers = (
            "text/plain; version=0.0.4",
            "text/plain;version=0.0.4",
            "version=0.0.4; text/plain",
        )

        for accept in headers:
            self.assertEqual(text.TextFormatter, negotiate(set(accept.split(";"))))

    def test_no_accept_header(self):
        """check request with no accept header works"""
        self.assertEqual(text.TextFormatter, negotiate(set()))
        self.assertEqual(text.TextFormatter, negotiate(set([""])))
