"""Report-only drift checks for config-backed page manifests."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

# Keep the documented ``python tools/manifest_lint.py`` invocation importable
# without requiring callers to modify PYTHONPATH.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.config_loader import load_config_mapping
from tools.config_pages import (
    ConfigPage,
    CoverPdfPage,
    GeneratedPage,
    PdfInsertPage,
    RstIncludePage,
)
from tools.lang_registry import canonical_language
from tools.page_manifest import resolve_config_pages_or_raise, resolve_page_manifest_path
from tools.utils.targets import format_tokenized


@dataclass(frozen=True)
class ManifestFinding:
    code: str
    severity: str
    config: str | None
    manifest: str | None
    message: str


@dataclass(frozen=True)
class ManifestLintReport:
    configs_scanned: int
    manifests_scanned: int
    findings: tuple[ManifestFinding, ...]

    def as_dict(self) -> dict[str, Any]:
        counts = Counter(finding.severity for finding in self.findings)
        return {
            "schema_version": "manifest-lint/v1",
            "configs_scanned": self.configs_scanned,
            "manifests_scanned": self.manifests_scanned,
            "summary": {key: counts.get(key, 0) for key in ("ERROR", "WARN")},
            "findings": [asdict(finding) for finding in self.findings],
        }


def _relative(path: Path | None, *, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _languages(values: Iterable[object]) -> set[str]:
    result: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        result.add(canonical_language(text) or text)
    return result


def _page_languages(pages: Iterable[ConfigPage]) -> set[str]:
    values: list[object] = []
    for page in pages:
        if isinstance(page, RstIncludePage):
            values.append(page.lang)
        elif isinstance(page, (GeneratedPage, PdfInsertPage)):
            values.extend(page.langs)
    return _languages(values)


def _page_source_values(page: ConfigPage) -> tuple[str, ...]:
    if isinstance(page, RstIncludePage):
        return (page.file,)
    if isinstance(page, GeneratedPage):
        return (page.recipe, page.template)
    if isinstance(page, CoverPdfPage):
        return (page.file,)
    if isinstance(page, PdfInsertPage):
        return tuple(page.file_map.values())
    return ()


def _config_languages(cfg: dict[str, Any]) -> set[str]:
    build = cfg.get("build", {})
    if not isinstance(build, dict):
        return set()
    values = build.get("languages", ["en"])
    return _languages(values if isinstance(values, list) else [values])


def _config_target(cfg: dict[str, Any], key: str) -> str | None:
    build = cfg.get("build", {})
    if not isinstance(build, dict):
        return None
    value = build.get(key)
    text = str(value).strip() if value is not None else ""
    return text or None


def _docs_dir(cfg: dict[str, Any], *, root: Path) -> Path:
    paths = cfg.get("paths", {})
    raw = paths.get("docs_dir") if isinstance(paths, dict) else None
    path = Path(str(raw).strip()) if isinstance(raw, str) and raw.strip() else Path("docs")
    return path if path.is_absolute() else root / path


def _source_findings(
    pages: Iterable[ConfigPage],
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    config_rel: str,
    manifest_rel: str,
    root: Path,
) -> list[ManifestFinding]:
    findings: list[ManifestFinding] = []
    for page_index, page in enumerate(pages, start=1):
        for raw_value in _page_source_values(page):
            if raw_value.startswith("asset:"):
                continue
            try:
                source_path = docs_dir / format_tokenized(raw_value, None, model, region)
            except RuntimeError as exc:
                findings.append(
                    ManifestFinding(
                        code="UNRESOLVED_SOURCE_TOKEN",
                        severity="WARN",
                        config=config_rel,
                        manifest=manifest_rel,
                        message=f"page {page_index}: {exc}",
                    )
                )
                continue
            if not source_path.exists():
                findings.append(
                    ManifestFinding(
                        code="MISSING_MANIFEST_SOURCE",
                        severity="WARN",
                        config=config_rel,
                        manifest=manifest_rel,
                        message=(
                            f"page {page_index}: source is missing: "
                            f"{_relative(source_path, root=root)}"
                        ),
                    )
                )
    return findings


def lint_repository(root: Path) -> ManifestLintReport:
    root = root.resolve()
    config_paths = sorted((root / "configs").glob("config*.yaml"))
    manifest_paths = sorted((root / "docs" / "manifests").glob("*.yaml"))
    findings: list[ManifestFinding] = []
    referenced: set[Path] = set()
    manifest_ids: dict[str, Path] = {}

    for config_path in config_paths:
        config_rel = _relative(config_path, root=root) or config_path.name
        try:
            cfg = load_config_mapping(config_path)
        except RuntimeError as exc:
            findings.append(
                ManifestFinding(
                    code="CONFIG_LOAD_ERROR",
                    severity="ERROR",
                    config=config_rel,
                    manifest=None,
                    message=str(exc),
                )
            )
            continue

        manifest_path = resolve_page_manifest_path(
            cfg,
            root=root,
            model=_config_target(cfg, "default_model"),
            region=_config_target(cfg, "default_region"),
        )
        if manifest_path is None:
            findings.append(
                ManifestFinding(
                    code="CONFIG_WITHOUT_MANIFEST",
                    severity="WARN",
                    config=config_rel,
                    manifest=None,
                    message="config has no paths.page_manifest reference",
                )
            )
            continue

        manifest_path = manifest_path.resolve()
        referenced.add(manifest_path)
        manifest_rel = _relative(manifest_path, root=root) or manifest_path.name
        if not manifest_path.exists():
            findings.append(
                ManifestFinding(
                    code="MISSING_MANIFEST",
                    severity="ERROR",
                    config=config_rel,
                    manifest=manifest_rel,
                    message="configured page manifest does not exist",
                )
            )
            continue

        try:
            resolved = resolve_config_pages_or_raise(
                cfg,
                default_languages=sorted(_config_languages(cfg)),
                root=root,
                model=_config_target(cfg, "default_model"),
                region=_config_target(cfg, "default_region"),
                error_prefix=f"{config_rel}.pages",
            )
        except RuntimeError as exc:
            findings.append(
                ManifestFinding(
                    code="INVALID_MANIFEST",
                    severity="ERROR",
                    config=config_rel,
                    manifest=manifest_rel,
                    message=str(exc),
                )
            )
            continue

        if resolved.manifest_id:
            previous = manifest_ids.get(resolved.manifest_id)
            if previous is not None and previous != manifest_path:
                findings.append(
                    ManifestFinding(
                        code="DUPLICATE_MANIFEST_ID",
                        severity="WARN",
                        config=config_rel,
                        manifest=manifest_rel,
                        message=(
                            f"manifest_id {resolved.manifest_id!r} is also used by "
                            f"{_relative(previous, root=root)}"
                        ),
                    )
                )
            else:
                manifest_ids[resolved.manifest_id] = manifest_path
        else:
            findings.append(
                ManifestFinding(
                    code="MANIFEST_ID_MISSING",
                    severity="WARN",
                    config=config_rel,
                    manifest=manifest_rel,
                    message="manifest has no non-empty manifest_id",
                )
            )

        expected_languages = _config_languages(cfg)
        actual_languages = _page_languages(resolved.pages)
        if expected_languages != actual_languages:
            findings.append(
                ManifestFinding(
                    code="LANGUAGE_SET_DRIFT",
                    severity="WARN",
                    config=config_rel,
                    manifest=manifest_rel,
                    message=(
                        f"config languages={sorted(expected_languages)} but manifest "
                        f"pages={sorted(actual_languages)}"
                    ),
                )
            )

        findings.extend(
            _source_findings(
                resolved.pages,
                docs_dir=_docs_dir(cfg, root=root),
                model=_config_target(cfg, "default_model"),
                region=_config_target(cfg, "default_region"),
                config_rel=config_rel,
                manifest_rel=manifest_rel,
                root=root,
            )
        )

    for manifest_path in manifest_paths:
        if manifest_path.resolve() not in referenced:
            findings.append(
                ManifestFinding(
                    code="ORPHAN_MANIFEST",
                    severity="WARN",
                    config=None,
                    manifest=_relative(manifest_path, root=root),
                    message="manifest is not referenced by any configs/config*.yaml",
                )
            )

    return ManifestLintReport(
        configs_scanned=len(config_paths),
        manifests_scanned=len(manifest_paths),
        findings=tuple(findings),
    )


def _render_text(report: ManifestLintReport) -> str:
    counts = Counter(finding.severity for finding in report.findings)
    lines = [
        "manifest-lint: report-only",
        f"configs={report.configs_scanned} manifests={report.manifests_scanned} "
        f"errors={counts.get('ERROR', 0)} warnings={counts.get('WARN', 0)}",
    ]
    for finding in report.findings:
        location = ":".join(part for part in (finding.config, finding.manifest) if part)
        lines.append(f"[{finding.severity}] {finding.code} {location}: {finding.message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report config/page-manifest drift without blocking builds")
    parser.add_argument("--root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--json", action="store_true", help="emit the machine-readable report")
    args = parser.parse_args(argv)

    report = lint_repository(args.root)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2) if args.json else _render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
