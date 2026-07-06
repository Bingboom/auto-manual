#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden-output regression net for the IDML exporter (componentization P0).

Builds the .idml package through the real CLI (``tools/export_idml.py``) from
committed fixtures and compares every zip part byte-for-byte against a
committed golden snapshot. Two variants:

- ``data_only``  — fixtures snapshot, no prepared bundle: the four data pages
  (spec / lcd / trouble / symbols) end to end.
- ``composed``   — fixtures snapshot + the synthetic bundle in
  ``tests/fixtures/idml_bundle``: prose stories, the safety twocol split, the
  safety+symbols merged page, the fcc+inbox merged page, components
  (safetywarning / warninglead / warnbox / notice / fcc / inbox / lcdmode),
  list-tables, and bold runs — i.e. the whole main() composition state machine.

Normalization: absolute ``file://`` image-link URIs are machine-dependent, so
the repo-root URI prefix is replaced with a placeholder before comparing.

Regenerating the golden (ONLY for an intentional output change — never to make
a refactor pass; during the componentization phases a golden diff means the
refactor changed behavior and must be fixed, not re-baselined):

    python tests/test_export_idml_golden.py --regenerate

then review the fixture diff like any other code change.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = ROOT / "tests" / "fixtures" / "idml_golden"
BUNDLE_FIXTURE = ROOT / "tests" / "fixtures" / "idml_bundle"
DATA_FIXTURE = ROOT / "tests" / "fixtures" / "phase2"
ROOT_URI = ROOT.resolve().as_uri()
URI_PLACEHOLDER = "file://IDML-GOLDEN-ROOT"

VARIANTS: dict[str, dict] = {
    # bundle-root pointing at a non-directory => data pages only
    "data_only": {"bundle_root": ROOT / "tests" / "fixtures" / "idml_bundle_absent"},
    "composed": {"bundle_root": BUNDLE_FIXTURE},
}


def _build_package(bundle_root: Path, out_path: Path) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "export_idml.py"),
        "--model", "JE-1000F",
        "--region", "US",
        "--lang", "en",
        "--data-root", str(DATA_FIXTURE),
        "--bundle-root", str(bundle_root),
        "--out", str(out_path),
    ]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def _normalized_parts(idml_path: Path) -> dict[str, bytes]:
    parts: dict[str, bytes] = {}
    with zipfile.ZipFile(idml_path) as zf:
        for name in zf.namelist():
            text = zf.read(name).decode("utf-8")
            parts[name] = text.replace(ROOT_URI, URI_PLACEHOLDER).encode("utf-8")
    return parts


def _golden_parts(variant: str) -> dict[str, bytes]:
    base = GOLDEN_ROOT / variant
    return {
        p.relative_to(base).as_posix(): p.read_bytes()
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


def _write_golden(variant: str, parts: dict[str, bytes]) -> None:
    base = GOLDEN_ROOT / variant
    if base.exists():
        for p in sorted(base.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
    for name, data in parts.items():
        dest = base / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


class IdmlGoldenTests(unittest.TestCase):
    maxDiff = 2000

    def _build_and_normalize(self, variant: str) -> dict[str, bytes]:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "golden.idml"
            proc = _build_package(VARIANTS[variant]["bundle_root"], out)
            self.assertEqual(
                proc.returncode, 0,
                f"exporter failed for {variant}:\n{proc.stdout}\n{proc.stderr}",
            )
            return _normalized_parts(out)

    def _assert_matches_golden(self, variant: str) -> None:
        golden = _golden_parts(variant)
        self.assertTrue(
            golden,
            f"no golden snapshot for {variant}; generate one with "
            "`python tests/test_export_idml_golden.py --regenerate`",
        )
        built = self._build_and_normalize(variant)
        self.assertEqual(
            sorted(built), sorted(golden),
            f"{variant}: package part list diverged from golden",
        )
        for name in sorted(golden):
            if built[name] != golden[name]:
                built_text = built[name].decode("utf-8")
                golden_text = golden[name].decode("utf-8")
                self.assertEqual(
                    golden_text, built_text,
                    f"{variant}/{name}: content diverged from golden",
                )

    def test_data_only_package_matches_golden(self) -> None:
        self._assert_matches_golden("data_only")

    def test_composed_package_matches_golden(self) -> None:
        self._assert_matches_golden("composed")

    def test_build_is_deterministic(self) -> None:
        first = self._build_and_normalize("composed")
        second = self._build_and_normalize("composed")
        self.assertEqual(first, second)


def _regenerate() -> int:
    for variant in VARIANTS:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "golden.idml"
            proc = _build_package(VARIANTS[variant]["bundle_root"], out)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr, file=sys.stderr)
                print(f"[golden] FAILED building {variant}", file=sys.stderr)
                return 1
            parts = _normalized_parts(out)
            _write_golden(variant, parts)
            print(f"[golden] wrote {len(parts)} parts -> {GOLDEN_ROOT / variant}")
    return 0


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        raise SystemExit(_regenerate())
    unittest.main()
