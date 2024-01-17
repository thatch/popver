import tempfile
from pathlib import Path
from unittest import TestCase

from click.testing import CliRunner
from packaging.utils import canonicalize_name
from pypi_simple import NoSuchProjectError
from pypi_simple.classes import ProjectPage

from ..cli import expand, get_version_and_requires_python, main


class FakePyPISimple:
    def __init__(self, fixture_dir: str) -> None:
        self.fixture_dir = Path("popver", "tests", fixture_dir).resolve()

    def get_project_page(self, project: str):
        try:
            data = (
                self.fixture_dir / (canonicalize_name(project) + ".html")
            ).read_text()
        except OSError:
            raise NoSuchProjectError(
                project, f"{self.fixture_dir}/{project}.html"
            ) from None

        return ProjectPage.from_html(project, data)


class CliTest(TestCase):
    def test_basic(self):
        runner = CliRunner()
        result = runner.invoke(main, ["requests"])
        self.assertEqual(0, result.exit_code)
        # TODO improve
        assert "1 3.7      100.0%" in result.output

    def test_expand(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"a\nb\n")
            f.flush()
            self.assertEqual(["a", "b", "c"], list(expand(["@" + f.name, "c"])))

    def assertVersionMatch(self, rv, name, ver, rp):
        self.assertEqual((name, ver, rp), (rv[0], rv[1].version, rv[2]))

    def test_public_private(self):
        A = FakePyPISimple("data")
        B = FakePyPISimple("private")

        with self.subTest("Normal"):
            rv = get_version_and_requires_python(
                public=A, private=None, show=None, project="Requests"
            )
            # N.b. name does not get normalized here
            self.assertVersionMatch(rv, "Requests", "2.31.0", ">=3.7")

        with self.subTest("Show public (only)"):
            rv = get_version_and_requires_python(
                public=A, private=None, show="public", project="requests"
            )
            self.assertVersionMatch(rv, "requests", "2.31.0", ">=3.7")

        with self.subTest("Show public"):
            # Just public, while also providing an private that doesn't have it
            rv = get_version_and_requires_python(
                public=A, private=B, show="public", project="requests"
            )
            self.assertVersionMatch(rv, "requests", "2.31.0", ">=3.7")
            rv = get_version_and_requires_python(
                public=A, private=B, show="private", project="requests"
            )
            self.assertEqual(None, rv)

        with self.subTest("Only private"):
            # This library (fake name) is only in private.
            rv = get_version_and_requires_python(
                public=A, private=B, show="public", project="private-circular"
            )
            self.assertEqual(None, rv)
            rv = get_version_and_requires_python(
                public=A, private=B, show="private", project="private-circular"
            )
            self.assertVersionMatch(rv, "private-circular", "0.1", ">=3.4")

        with self.subTest("Neither"):
            rv = get_version_and_requires_python(
                public=A, private=B, show="public", project="zzz"
            )
            self.assertEqual(None, rv)

        with self.subTest("No versions"):
            rv = get_version_and_requires_python(
                public=A, private=B, show=None, project="foo"
            )
            self.assertEqual(None, rv)
