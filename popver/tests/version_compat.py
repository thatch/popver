from unittest import TestCase

from ..version_compat import understand


class UnderstandTest(TestCase):
    def test_all(self):
        self.assertEqual("?", understand(None))

        self.assertEqual(
            "any", understand("")
        )  # I think there is one in the wild, but uncommon

        self.assertEqual("3.6", understand(">=3.6"))
        self.assertEqual("3.6", understand(">3.5,!=3.5.*"))

        # error
        self.assertEqual("X", understand("Z"))
        self.assertEqual("none?", understand("<2.7"))
