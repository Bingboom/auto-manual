"""Generate a review-only reference-layout contract draft."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tools.idml.reference_layout_scaffold import build_reference_layout_scaffold
from tools.idml.reference_layout_plan import ReferenceLayoutPlanError
from tools.manual_ir import read_manual_ir


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-plan", type=Path, required=True)
    parser.add_argument("--manual-ir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    try:
        candidate = build_reference_layout_scaffold(
            args.seed_plan,
            read_manual_ir(args.manual_ir),
        )
        output = args.output.resolve()
        if output.exists() and not args.force:
            parser.error(f"output exists; pass --force to replace: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, ReferenceLayoutPlanError) as exc:
        parser.error(str(exc))

    print(
        "REFERENCE-LAYOUT SCAFFOLD: draft "
        f"target={candidate['target']['model']}/{candidate['target']['region']} "
        f"pages={candidate['reference_pdf']['page_count']} "
        "production_eligible=false registry_update=required-after-approval"
    )
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
