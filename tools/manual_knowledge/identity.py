"""Stable manual-variant identity and callout severity for the EU machine corpus.

Identity has two layers: ``variant_key`` (model/region/language) stays stable
across releases, while ``revision`` names one printed manual revision. Git
technical snapshots (``git-…``) are publication versions, not revisions.
"""
from __future__ import annotations

import re

GENERATOR_VERSION = "manual-knowledge/1.1"
MACHINE_SURFACE = {"source_kind": "published_html", "generation_mode": "html_compatibility",
                   "target_mode": "same_source_native", "generator_version": GENERATOR_VERSION}
_PRINTED = re.compile(r"\d+(?:\.\d+)*")

_SEVERITY_LABELS = {
    "warning": "WARNING WARNUNG AVERTISSEMENT AVVERTENZA ADVERTENCIA AVISO WAARSCHUWING OSTRZEŻENIE ПОПЕРЕДЖЕННЯ",
    "caution": "CAUTION VORSICHT ATTENTION ATTENZIONE PRECAUCIÓN CUIDADO OPGELET PRZESTROGA УВАГА",
    "note": ("NOTE NOTES HINWEIS HINWEISE REMARQUE REMARQUES NOTA NOTAS OPMERKING OPMERKINGEN "
             "UWAGA UWAGI ПРИМІТКА ПРИМІТКИ OBSERVACIONES"),
    "tip": "TIP TIPS TIPP CONSEJOS CONSEILS SUGGERIMENTO DICA DICAS WSKAZÓWKA WSKAZÓWKI ПОРАДИ",
}
SEVERITY = {label.casefold(): severity for severity, labels in _SEVERITY_LABELS.items()
            for label in labels.split()}


def callout_severity(label: str) -> str:
    """Map a localized callout label to a fixed severity; never guess the rest."""
    key = label.strip().lstrip("*").strip().rstrip(":").strip().casefold()
    return SEVERITY.get(key, "unknown")


def revision_of(version: object) -> tuple[str | None, str]:
    """Split a publication version into a printed revision and its kind."""
    if not isinstance(version, str) or not version.strip():
        return None, "unclassified"
    if version.startswith("git-"):
        return None, "technical_snapshot"
    if version == "candidate":
        return None, "candidate"
    if _PRINTED.fullmatch(version):
        return version, "printed"
    return None, "unclassified"


def variant_identity(*, model: str, region: str, lang: str | None, version: object) -> dict:
    """Stable variant key plus the revision this edition was published as."""
    language = lang or "multi"
    key = f"{model}/{region}/{language}"
    revision, kind = revision_of(version)
    return {"variant_key": key, "manual_variant_id": f"{key}@{revision or version or 'unversioned'}",
            "language": language, "language_status": "verified" if lang else "needs_review",
            "revision": revision, "revision_kind": kind,
            "publication_version": version if isinstance(version, str) else None}
