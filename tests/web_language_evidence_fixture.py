from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from tools.web_language_release_evidence import capture_projection, seal_release_evidence


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_projection_fixture(
    bundle: Path, *, model: str, region: str, language: str
) -> Path:
    page = bundle / "page" / f"manual_{language}.rst"
    page.parent.mkdir(parents=True)
    (bundle / "index.rst").write_text(
        f".. include:: page/manual_{language}.rst\n", encoding="utf-8"
    )
    page.write_text(f"\\HBApplyLang{{{language}}}\n", encoding="utf-8")
    manifest = bundle / "bundle_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "web-language-bundle/v1",
                "model": model,
                "region": region,
                "language": language,
                "source_index_sha256": "a" * 64,
                "source_pages": [
                    {"path": page.relative_to(bundle).as_posix(), "sha256": _sha256(page)}
                ],
                "pages": [
                    {"path": page.relative_to(bundle).as_posix(), "sha256": _sha256(page)}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def seal_language_evidence_fixture(
    *,
    markdown_dir: Path,
    markdown_name: str,
    html_dir: Path,
    evidence_dir: Path,
    model: str,
    region: str,
    language: str,
    version: str,
    git_ref: str,
) -> tuple[Path, str]:
    with tempfile.TemporaryDirectory() as td:
        bundle = Path(td) / "rst"
        manifest = write_projection_fixture(
            bundle, model=model, region=region, language=language
        )
        captures = tuple(
            capture_projection(
                manifest,
                action=action,
                model=model,
                region=region,
                language=language,
            )
            for action in ("check", "md", "html")
        )
        nested_evidence = evidence_dir.resolve(strict=False).is_relative_to(
            markdown_dir.resolve(strict=False)
        )
        seal_dir = Path(td) / "evidence" if nested_evidence else evidence_dir
        receipt = seal_release_evidence(
            captures=captures,
            markdown_dir=markdown_dir,
            markdown_name=markdown_name,
            html_dir=html_dir,
            evidence_dir=seal_dir,
            version=version,
            git_ref=git_ref,
        )
        if nested_evidence:
            shutil.copytree(seal_dir, evidence_dir)
            receipt = evidence_dir / receipt.name
    return receipt, _sha256(receipt)
