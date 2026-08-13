from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable


def collect_fcc_renderer_contract_issues(
    *,
    bundle_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
    issue_cls: type[Any],
    convert_rst_fragment_to_html: Callable[..., str],
) -> list[Any]:
    """Fail ``check`` before Word/Web generation when FCC structure drifts."""

    page_dir = bundle_dir / "page"
    if not page_dir.exists():
        return []

    active_tags = {
        f"region_{region_name.strip().lower().replace('-', '_')}"
        for region_name in (region,)
        if region_name and region_name.strip()
    }
    issues: list[Any] = []
    for source_path in sorted(page_dir.glob("*01_fcc.rst")):
        rst_text = source_path.read_text(encoding="utf-8")
        for profile in ("document", "web"):
            try:
                with TemporaryDirectory(prefix="auto-manual-check-fcc-") as tmp:
                    convert_rst_fragment_to_html(
                        rst_text,
                        source_path,
                        Path(tmp),
                        active_tags=active_tags,
                        presentation_profile=profile,
                        model=model,
                        region=region,
                        language=lang,
                    )
            except Exception as exc:
                issues.append(
                    issue_cls(
                        code="FCC_RENDER_CONTRACT",
                        message=f"FCC {profile} renderer contract failed: {exc}",
                        model=model,
                        region=region,
                        path=source_path,
                        lang=lang,
                    )
                )
    return issues


__all__ = ["collect_fcc_renderer_contract_issues"]
