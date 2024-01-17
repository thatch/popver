from unittest import TestCase

from ..selection import get_sort_key, select_package
from .metadata import OLD_WHEEL_PKG, SDIST_TARGZ_PKG, WHEEL_PKG


class SelectionTest(TestCase):
    def test_empty(self):
        self.assertEqual(None, select_package([]))

    def test_prefer_wheel(self):
        self.assertEqual(WHEEL_PKG, select_package([SDIST_TARGZ_PKG, WHEEL_PKG]))

    def test_prefer_newer_wheel(self):
        self.assertEqual(WHEEL_PKG, select_package([OLD_WHEEL_PKG, WHEEL_PKG]))

    def test_prefer_newer_sdist(self):
        self.assertEqual(
            SDIST_TARGZ_PKG, select_package([OLD_WHEEL_PKG, SDIST_TARGZ_PKG])
        )
