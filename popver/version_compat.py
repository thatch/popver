from typing import Optional

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

# Key is a display string, value is a Version object to check against the match.
# These should be ordered from least to most restrictive
VERSIONS = {
    "py3": Version("3.0a1"),
    "2.7": Version("2.7.99"),
    "3.1": Version("3.1.99"),
    "3.2": Version("3.2.99"),
    "3.3": Version("3.3.99"),
    "3.4": Version("3.4.99"),
    "3.5": Version("3.5.99"),
    "3.6": Version("3.6.99"),
    "3.7": Version("3.7.99"),
    "3.8": Version("3.8.99"),
    "3.9": Version("3.9.99"),
    "3.10": Version("3.10.99"),
    "3.11": Version("3.11.99"),
    "3.12": Version("3.12.99"),
    "3.13": Version("3.13.99"),
    "3.14": Version("3.14.99"),
    "3.15": Version("3.15.99"),
}


def understand(rp: Optional[str]) -> str:
    if rp is None:
        return "?"

    if not rp.strip():
        return "any"

    try:
        s = SpecifierSet(rp)
    except InvalidSpecifier:
        return "X"

    for v, x in VERSIONS.items():
        if x in s:
            return v

    return "none?"
