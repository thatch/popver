import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from functools import partial
from typing import Generator, Iterable, List, Optional, Tuple

import click
from indexurl import get_index_url
from keke import kev, ktrace, TraceOutput
from pypi_simple import NoSuchProjectError, PyPISimple

from .metadata import (
    get_metadata,
    get_metadata_bytes,
    infer_requires_python_from_dist,
    SESSION,
)
from .selection import select_package
from .version_compat import understand, VERSIONS


def expand(lst: Iterable[str]) -> Generator[str, None, None]:
    for item in lst:
        if item.startswith("@"):
            with open(item[1:]) as f:
                for line in f:
                    # Technically the BOM is only at the beginning of the file, but this is easy.
                    yield line.strip().replace("\ufeff", "")
        else:
            yield item


# Split out for easier timing and use with a threadpool
@ktrace("project")
def get_version_and_requires_python(public, private, show, project):
    try:
        with kev("private"):
            page = private.get_project_page(project)
        if show == "public":
            return
    except (AttributeError, NoSuchProjectError):
        try:
            with kev("public"):
                page = public.get_project_page(project)
            if show == "private":
                return
        except NoSuchProjectError:
            return

    package = select_package(page.packages)
    if package is None:
        # TODO: Categorize these separately; such projects have no known versions
        return

    requires_python = infer_requires_python_from_dist(package)
    return (project, package, requires_python)


@click.group()
@click.pass_context
@click.option(
    "--trace",
    metavar="FILE",
    type=click.File("w"),
    help="Write chrome trace to this filename",
)
def main(ctx, trace):
    if trace:
        ctx.with_resource(TraceOutput(trace))


@main.command(help="Find metadata")
@click.argument("package_name")
def md(package_name: str) -> None:
    public = PyPISimple(get_index_url(), session=SESSION)
    with kev("fetch", package_name=package_name):
        page = public.get_project_page(package_name)
    best = select_package(page.packages)
    if best:
        md = get_metadata_bytes(best)
        sys.stdout.write(md.decode())


@main.command(help="Find deps from metadata")
@click.argument("package_names", nargs=-1)
def deps(package_names: Tuple[str]) -> None:
    public = PyPISimple(get_index_url(), session=SESSION)
    for name in package_names:
        with kev("fetch", package_name=name):
            page = public.get_project_page(name)
        best = select_package(page.packages)
        if best:
            md = get_metadata(best)
            print(name, md.get_all("requires-dist"))


@main.command(help="Analyze requires_python")
@click.option(
    "--private-index",
    type=str,
    default=None,
    help="An optional url to a private simple/ index",
)
@click.option(
    "--show",
    type=str,
    default=None,
    help="Can be set to 'public' or 'private' to only show those cohort stats, otherwise mixed",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Display messages as projects are looked up"
)
@click.argument("projects", nargs=-1)
def requires_python(
    projects: List[str],
    verbose: bool,
    show: Optional[str],
    trace: Optional[str],
    private_index: Optional[str],
) -> None:
    public = PyPISimple()
    private = None
    if private_index:
        private = PyPISimple(private_index)

    counts = defaultdict(lambda: 0)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(
            partial(get_version_and_requires_python, public, private, show),
            expand(projects),
        ):
            if result is None:
                continue

            (project, package, requires_python) = result

            if requires_python is None:
                r = "?"
                if verbose:
                    print("->", package.url, "no version info")
            else:
                r = understand(requires_python)

            counts[r] += 1
            if verbose:
                print(project, r, package.version)

    if verbose:
        print()

    keys = {k: i for i, k in enumerate(VERSIONS)}
    total = sum(counts.values())
    sofar = 0

    FMT = "%8s %-8s %6s %6s"

    print(FMT % ("count", "minver", "cdf1", "cdf2"))
    for k, v in sorted(counts.items(), key=lambda i: keys.get(i[0], -1)):
        sofar += v
        print(
            FMT
            % (
                v,
                k,
                "%.1f%%" % (sofar * 100 / total),
                "%.1f%%" % ((total - sofar) * 100 / total),
            )
        )

    print()
    print(
        "cdf1: Fraction of libs available to this version of python (carrot, add new ones)"
    )
    print(
        "cdf2: Fraction of libs unavailable if this is the newest you have (stick, remove old ones as they are less useful)"
    )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
