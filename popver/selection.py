from typing import Iterable, Optional, Tuple

from keke import ktrace
from packaging.version import InvalidVersion, Version
from pypi_simple import DistributionPackage

GOODNESS = {
    "wheel": 3,
    "sdist": 2,
    "bdist": 1,
}


@ktrace()
def select_package(
    packages: Iterable[DistributionPackage],
) -> Optional[DistributionPackage]:
    """
    Returns the most-likely-to-have-metadata package from the given `DistributionPackage`s
    while attempting to mirror the selection that pip would make.
    """

    best: Optional[Tuple[bool, Version, bool, bool, str, DistributionPackage]] = None
    for package in packages:
        if package.is_yanked:
            continue
        if package.version is None:
            continue
        try:
            v = Version(package.version)
        except InvalidVersion:
            continue

        sort_key = get_sort_key(package, v)
        if best is None or sort_key > best:
            best = sort_key

    if best is None:
        return None
    return best[-1]


def get_sort_key(package, v):
    # TODO dev and post
    return (
        not v.is_prerelease,
        v,
        GOODNESS.get(package.package_type, 0),
        package.filename.endswith(".zip"),
        package.filename,
        package.url,  # hopefully enough to break ties
        package,
    )
