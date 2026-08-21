from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.manifest_family import (
    SCHEMA_VERSION,
    ManifestDiffError,
    apply_manifest_diff,
    build_manifest_diff,
    canonical_manifest_bytes,
    fold_repository,
    load_manifest,
    main,
    roundtrip_report,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "docs" / "manifests"


class ManifestFamilyTests(unittest.TestCase):
    def test_family_index_folds_all_18_manifest_goldens(self) -> None:
        # 18 manifests / 3 anchors / 15 folded: the third anchor is the BP@INTL
        # resolved manifest (skeleton-library slice S1), which has no diff
        # entries — anchors are bases, not fold targets.
        report = fold_repository(
            ROOT,
            MANIFESTS / "family" / "index.yaml",
        )
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(18, report["manifest_count"])
        self.assertEqual(3, report["anchor_count"])
        self.assertEqual(15, report["folded_count"])
        self.assertTrue(all(item["byte_identical"] for item in report["checks"]))

    def test_two_us_single_language_pilot_lines_roundtrip_byte_identically(self) -> None:
        for target_name in ("manual_us-single-fr.yaml", "manual_us-single-es.yaml"):
            base = load_manifest(MANIFESTS / "manual_us-single-en.yaml")
            target = load_manifest(MANIFESTS / target_name)
            diff = build_manifest_diff(base, target)
            rebuilt = apply_manifest_diff(base, diff)

            self.assertEqual(SCHEMA_VERSION, diff["schema_version"])
            self.assertEqual(canonical_manifest_bytes(target), canonical_manifest_bytes(rebuilt))
            self.assertTrue(roundtrip_report(base, target, diff)["byte_identical"])

    def test_diff_is_deterministic_and_rejects_the_wrong_base(self) -> None:
        base = {
            "manifest_id": "base",
            "pages": [{"type": "rst_include", "lang": "en", "file": "intro.rst"}],
        }
        target = {
            "manifest_id": "target",
            "pages": [{"type": "rst_include", "lang": "fr", "file": "intro_fr.rst"}],
        }
        first = build_manifest_diff(base, target)
        second = build_manifest_diff(base, target)
        self.assertEqual(first, second)
        with self.assertRaisesRegex(ManifestDiffError, "does not match"):
            apply_manifest_diff({**base, "manifest_id": "other"}, first)

    def test_cli_writes_and_consumes_json_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base_path = root / "base.yaml"
            target_path = root / "target.yaml"
            diff_path = root / "family.diff.json"
            base_path.write_text(
                "manifest_id: base\npages:\n  - type: rst_include\n    lang: en\n    file: intro.rst\n",
                encoding="utf-8",
            )
            target_path.write_text(
                "manifest_id: target\npages:\n  - type: rst_include\n    lang: fr\n    file: intro_fr.rst\n",
                encoding="utf-8",
            )

            self.assertEqual(
                0,
                main(
                    [
                        "diff",
                        "--base",
                        str(base_path),
                        "--target",
                        str(target_path),
                        "--output",
                        str(diff_path),
                    ]
                ),
            )
            diff = json.loads(diff_path.read_text(encoding="utf-8"))
            self.assertEqual(SCHEMA_VERSION, diff["schema_version"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    0,
                    main(
                        [
                            "roundtrip",
                            "--base",
                            str(base_path),
                            "--target",
                            str(target_path),
                            "--diff",
                            str(diff_path),
                        ]
                    ),
                )
            self.assertIn('"byte_identical": true', output.getvalue())


if __name__ == "__main__":
    unittest.main()
