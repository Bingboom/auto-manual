"""Which half of the portal a build makes, failing closed on Read the Docs.

One frozen source feeds two Read the Docs projects: the private project builds
the combined site (manuals plus the knowledge base) and every other project
builds the manuals only. ``RTD_SITE_ROLE`` (Sphinx config ``rtd_site_role``)
still selects a role, but on Read the Docs only a project listed in
:data:`PRIVATE_RTD_PROJECTS` may build the combined site. Any other project
builds ``manuals`` even when the variable is missing, and asking it for
``combined`` fails the build. A forgotten variable on a new or public project
therefore cannot publish the knowledge base. Adding a private project is a
reviewed change to that list.

The role decides what a build contains, not who can open it: that is each
project's privacy level in Read the Docs. Local builds keep the old default,
``combined``.
"""
from __future__ import annotations

from collections.abc import Mapping

SITE_ROLES = ("combined", "manuals")
# Read the Docs project slugs (READTHEDOCS_PROJECT) that may build the knowledge base.
PRIVATE_RTD_PROJECTS = frozenset({"ht-docs-ht-manuals"})
_TRUE = {"true", "1", "yes"}


def on_read_the_docs(environ: Mapping[str, str]) -> bool:
    """Read the Docs exports READTHEDOCS=True and the project slug to every build."""
    return environ.get("READTHEDOCS", "").strip().lower() in _TRUE or bool(environ.get("READTHEDOCS_PROJECT", "").strip())


def resolve_site_role(requested: str | None, environ: Mapping[str, str]) -> tuple[str, str]:
    """The build's role and the reason, for the build log.

    ``requested`` is ``rtd_site_role`` (from ``RTD_SITE_ROLE``); empty means unset.
    An unknown role always fails the build.
    """
    role = (requested or "").strip().lower()
    if role and role not in SITE_ROLES:
        raise ValueError(f"rtd_site_role must be one of {SITE_ROLES}, got {requested!r}")
    if not on_read_the_docs(environ):
        return role or "combined", "local build"
    project = environ.get("READTHEDOCS_PROJECT", "").strip()
    if project in PRIVATE_RTD_PROJECTS:
        return role or "combined", f"Read the Docs project {project} is listed as private"
    if role == "combined":
        raise ValueError(
            f"Read the Docs project {project or '(unknown)'!r} is not listed as private, so it cannot build the "
            "combined site with the knowledge base; add its slug to PRIVATE_RTD_PROJECTS in tools/rtd/site_role.py "
            "through a reviewed PR, or set RTD_SITE_ROLE=manuals")
    return "manuals", f"Read the Docs project {project or '(unknown)'} is not listed as private"
