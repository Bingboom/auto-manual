"""Fresh EU/UK publication admission, separate from immutable historical replay."""
from __future__ import annotations

from pathlib import Path

from tools.language_aliases import normalize_language
from tools.manual_ir import read_manual_ir
from tools.prepared_component_coverage import audit_prepared_component_coverage
from tools.prepared_component_policy import resolve_prepared_component_policy
from tools.utils.path_utils import PathSegments
from tools.web_document_ir import render_document_fragments
from tools.web_language_baseline import require_language_baseline


ADMITTED_REGIONS = frozenset({"EU", "UK", "EUUK"})


def require_fresh_component_admission(
    markdown_dir: Path, *, model: str, region: str, language: str | None, stored: bool = False,
) -> dict | None:
    """Reject missing IR, withdrawn bindings and changed legacy debt at ingress.

    Region scope is explicit. Other regions keep their existing admission
    rules. No candidate metadata marker can disable these checks. Historical
    evidence verifiers explicitly pass stored=True after checking their sealed
    inventories; that flag is never derived from candidate IR metadata.
    """
    if stored or region not in ADMITTED_REGIONS:
        return None
    path = Path(markdown_dir) / PathSegments.MANUAL_IR_JSON
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("fresh EU/UK Web publication requires a real manual IR sidecar")
    try:
        ir = read_manual_ir(path)
        expected_language = normalize_language(language) if language else ir.language
        if (ir.model, ir.region, ir.language) != (model, region, expected_language):
            raise ValueError("fresh component admission target identity mismatch")
        if ir.metadata.get("pending_source_review") or ir.metadata.get("publication_eligible") is False:
            raise ValueError("manual IR has pending source review")
        raw = ir.to_dict()
        baseline_report = require_language_baseline(raw, Path(markdown_dir))
        if ir.source == "prepared-document":
            policy = resolve_prepared_component_policy(model=model, region=region, language=ir.language)
            report = audit_prepared_component_coverage(raw, policy)
            if report["issues"]:
                raise ValueError("shared component admission failed: " + "; ".join(report["issues"]))
        elif ir.source in {"frozen-pdf-json", "frozen-ai-json"}:
            # The native gate is owned by the preceding native-admission change.
            from tools.frozen_web_component_coverage import require_frozen_component_coverage

            require_frozen_component_coverage(raw)
            report = {"profile": "native-shared-components", "issues": []}
        else:
            raise ValueError(f"unsupported fresh Web component source: {ir.source}")
        # Validate ComponentSpec slots and actual packaged asset bytes, even
        # when candidate inventory/coverage markers were removed or rehashed.
        render_document_fragments(ir, package_root=Path(markdown_dir))
        report["language_baseline"] = baseline_report
        if baseline_report["status"] == "not_enrolled":
            print(f"[language-baseline] {baseline_report['target']}: not_enrolled (English inheritance not covered)")
        return report
    except (ValueError, OSError) as exc:
        raise RuntimeError(str(exc)) from exc
