import email
import functools
from email.message import Message
from http.client import HTTPResponse
from io import BytesIO, StringIO

from tarfile import TarFile
from typing import Optional
from zipfile import ZipFile

from keke import kev, ktrace
from pypi_simple import DistributionPackage
from requests import Session
from seekablehttpfile import SeekableHttpFile
from seekablehttpfile.core import get_range_requests

SESSION = Session()
get_range_requests_session = functools.partial(get_range_requests, session=SESSION)


@ktrace("dp.filename", "dp.url")
def get_metadata_bytes(dp: DistributionPackage) -> bytes:
    if dp.has_metadata:
        with kev("get .metadata"):
            return SESSION.get(dp.url + ".metadata").content

    # This mirrors some logic from pkginfo, but returns the contents rather
    # than a dict-like object.
    if dp.package_type == "wheel":
        # print("W", dp.url)
        f = SeekableHttpFile(dp.url, get_range=get_range_requests_session)
        zf = ZipFile(f)
        # This snippet comes from warehouse itself.
        name, version, _ = dp.filename.split("-", 2)
        return zf.read(f"{name}-{version}.dist-info/METADATA")
    elif dp.package_type == "sdist":
        if dp.filename.endswith(".zip"):
            # print("SD", dp.url)
            f = SeekableHttpFile(dp.url, get_range=get_range_requests_session)
            zf = ZipFile(f)
            # Warehouse says this must only have one slash.
            metadata_names = [
                name
                for name in zf.namelist()
                if name.endswith("/PKG-INFO") and name.count("/") == 1
            ]
            metadata_names.sort(key=lambda x: (x.count("/"), len(x)))
            return zf.read(metadata_names[0])
        else:
            # print("ST", dp.url)
            data = BytesIO(SESSION.get(dp.url).content)
            archive = TarFile.open(fileobj=data)
            # Warehouse says this must only have one slash.
            metadata_names = [
                name
                for name in archive.getnames()
                if name.endswith("/PKG-INFO") and name.count("/") == 1
            ]
            metadata_names.sort(key=lambda x: (x.count("/"), len(x)))
            return archive.extractfile(metadata_names[0]).read()
    else:
        raise NotImplemented(dp.url)


def get_metadata(dp: DistributionPackage) -> Message:
    return email.message_from_bytes(get_metadata_bytes(dp))


PY_VER_CLASSIFIER_PREFIX = "Programming Language :: Python :: "


def infer_requires_python_from_dist(dp: DistributionPackage) -> Optional[str]:
    # Sometimes the index serves Requires-Python to us
    if dp.requires_python is not None:
        return dp.requires_python

    # Sometimes we need to go download a file to find Requires-Python
    md = get_metadata(dp)

    # This has been a way to declare compatibility since ~2005 and py2.7
    rp = md.get("Requires-Python")
    if rp is not None:
        return rp

    # Sometimes we have to look at classifiers and guess.  This has been a way
    # ~forever.
    classifiers = md.get_all("Classifier")
    if classifiers is not None:
        version_classifiers = [
            x[len(PY_VER_CLASSIFIER_PREFIX) :]
            for x in classifiers
            if x.startswith(PY_VER_CLASSIFIER_PREFIX) and "." in x
        ]
        if version_classifiers:
            # Assumes they're sorted
            return ">=" + version_classifiers[0]

    if "-py2.py3-" in dp.filename:
        # Call this 2.7+ if we didn't find any more specific hints above.
        # That's the last 2.x version, and the only one that might be necessary
        # for my use-case.
        return ">=2.7"

    # Intentionally don't default to something here for -py3- wheels; we don't
    # know the earliest version they support, in the same way we do for
    # -py2.py3- ones.
    return None
