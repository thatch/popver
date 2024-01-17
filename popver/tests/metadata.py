from unittest import mock, TestCase

from pypi_simple import DistributionPackage

from ..metadata import infer_requires_python_from_dist

OLD_WHEEL_PKG = DistributionPackage(
    filename="seekablehttpfile-0.0.3-py3-none-any.whl",
    project="seekablehttpfile",
    version="0.0.3",
    package_type="wheel",
    digests=None,
    requires_python=None,
    has_sig=False,
    url="https://files.pythonhosted.org/packages/d3/ff/bc80f151f5cdf8f71a01acc0df75cedad03a4bce28775a187ec82f0542fb/seekablehttpfile-0.0.3-py3-none-any.whl",
)

WHEEL_PKG = DistributionPackage(
    filename="seekablehttpfile-0.0.4-py3-none-any.whl",
    project="seekablehttpfile",
    version="0.0.4",
    package_type="wheel",
    digests=None,
    requires_python=None,
    has_sig=False,
    url="https://files.pythonhosted.org/packages/86/ea/f27b648330abff7d07faf03f2dbe8070630d2a14b79185f165d555447071/seekablehttpfile-0.0.4-py3-none-any.whl",
)

PY23_WHEEL_PKG = DistributionPackage(
    filename="toml-0.10.1-py2.py3-none-any.whl",
    project="toml",
    version="0.10.1",
    package_type="wheel",
    digests=None,
    requires_python=None,
    has_sig=False,
    url="https://files.pythonhosted.org/packages/9f/e1/1b40b80f2e1663a6b9f497123c11d7d988c0919abbf3c3f2688e448c5363/toml-0.10.1-py2.py3-none-any.whl",
)

SDIST_TARGZ_PKG = DistributionPackage(
    filename="seekablehttpfile-0.0.4.tar.gz",
    project="seekablehttpfile",
    version="0.0.4",
    package_type="sdist",
    digests=None,
    requires_python=None,
    has_sig=False,
    url="https://files.pythonhosted.org/packages/ad/8d/525109c3eb2ac7cd364fe8c20c3f5bf47a8c1f6b48d2b43deeeadaf4109a/seekablehttpfile-0.0.4.tar.gz",
)

SDIST_ZIP_PKG = DistributionPackage(
    filename="azure-common-1.1.28.zip",
    project="azure-common",
    version="1.1.28",
    package_type="sdist",
    digests=None,
    requires_python=None,
    has_sig=False,
    url="https://files.pythonhosted.org/packages/3e/71/f6f71a276e2e69264a97ad39ef850dca0a04fce67b12570730cb38d0ccac/azure-common-1.1.28.zip",
)


class MetadataTest(TestCase):
    # These two are more of an integration test, and require internet access
    def test_wheel(self):
        self.assertEqual(">=3.8", infer_requires_python_from_dist(WHEEL_PKG))

    def test_sdist_targz(self):
        self.assertEqual(">=3.8", infer_requires_python_from_dist(SDIST_TARGZ_PKG))

    def test_sdist_zip(self):
        self.assertEqual(">=2.7", infer_requires_python_from_dist(SDIST_ZIP_PKG))

    def test_classifiers(self):
        with mock.patch(
            "popver.metadata.get_metadata_bytes",
            return_value=b"Requires-Python: >=3.6\n",
        ):
            self.assertEqual(">=3.6", infer_requires_python_from_dist(SDIST_TARGZ_PKG))

    def test_classifiers(self):
        with mock.patch(
            "popver.metadata.get_metadata_bytes",
            return_value=(
                b"Classifier: Programming Language :: Python :: Implementation :: CPython\n"
                b"Classifier: Programming Language :: Python :: 3\n"
                b"Classifier: Programming Language :: Python :: 3.6\n"
            ),
        ):
            self.assertEqual(">=3.6", infer_requires_python_from_dist(SDIST_TARGZ_PKG))

        with mock.patch(
            "popver.metadata.get_metadata_bytes",
            return_value=b"Classifier: Foo\n",
        ):
            self.assertEqual(None, infer_requires_python_from_dist(SDIST_TARGZ_PKG))

        with mock.patch(
            "popver.metadata.get_metadata_bytes",
            return_value=b"\n",
        ):
            self.assertEqual(None, infer_requires_python_from_dist(SDIST_TARGZ_PKG))

    def test_py23(self):
        with mock.patch(
            "popver.metadata.get_metadata_bytes",
            return_value=b"\n",
        ):
            self.assertEqual(">=2.7", infer_requires_python_from_dist(PY23_WHEEL_PKG))
