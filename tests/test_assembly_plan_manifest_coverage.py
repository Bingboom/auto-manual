"""A frozen assembly plan must be reachable from the source that builds it.

A candidate `target_assembly` plan is frozen against a specific book: it names
every page, in order, and the exporter refuses anything else. So if the page
manifest for that target does not declare one of those pages, the target cannot
be built from its own source at all -- `build.py idml` prepares a bundle the
plan rejects, and the only way to the shipped package is an explicit
`--source review`, i.e. through a derivative that may not be reproducible.

JE-3000C_KR is in exactly that state today: its cover and back cover exist only
as authored files under `docs/_review`, and `docs/manifests/manual_kr.yaml`
declares neither. The pin below records that as known debt rather than pretending
it is fine -- and turns red the moment a *new* target joins it, or the moment KR
is fixed (then shrink the pin, the way the SKIP and warning ratchets work).

The check is static -- manifest text against plan text, no build -- so it runs in
milliseconds and covers every configured plan, including targets whose data is
not yet complete enough to build (JBP-2000B/EU).
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

from tools.build_paths import resolve_idml_assembly_plan
from tools.config_loader import load_config_mapping


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"

# Plan pages no manifest entry can produce. Empty means the target builds from
# its own source; a non-empty entry is debt, with the reason it is tolerated.
PINNED_UNDECLARED: dict[str, tuple[str, ...]] = {
    # Cover and back cover live only in docs/_review/JE-3000C/KR/ko/page/.
    # manual_kr.yaml is shared by JE-1000F_KR, JE-2000E_KR and JE-3000C_KR, so
    # declaring a per-model cover needs either a cover asset for all three or a
    # per-model manifest -- a product decision, not a code fix.
    "config.kr.yaml": (
        "page/cover_je3000c-ko.rst",
        "page/99_back_cover.rst",
    ),
    "config.bp-jp.yaml": (),
    "config.bp-us.yaml": (),
    "config.bp-eu.yaml": (),
}


def configs_with_a_plan() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for config in sorted(CONFIGS.glob("config.*.yaml")):
        paths_cfg = load_config_mapping(config).get("paths", {})
        if not isinstance(paths_cfg, dict):
            continue
        if "idml_assembly_plan" not in paths_cfg and "idml_assembly_plans" not in paths_cfg:
            continue
        by_target = paths_cfg.get("idml_assembly_plans")
        if isinstance(by_target, dict):
            for target, raw in sorted(by_target.items()):
                model, _, region = str(target).partition("_")
                plan = resolve_idml_assembly_plan(
                    config, repo_root=ROOT, model=model, region=region
                )
                if plan is not None:
                    found[config.name] = plan
            continue
        plan = resolve_idml_assembly_plan(config, repo_root=ROOT)
        if plan is not None:
            found[config.name] = plan
    return found


def declared_names(manifest: Path) -> tuple[set[str], set[str]]:
    """Bundle page names a manifest can produce.

    Two shapes, because a bundle page is named either after its template file
    or after the slot/data key that generated it: `rst_include` keeps the
    template basename, while `cover_pdf`, `csv_page`, `generated_page` and
    every slot-based entry name the page from `slot_id` / `page`.
    """

    payload = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    files: set[str] = set()
    keys: set[str] = set()
    for page in payload.get("pages") or []:
        if not isinstance(page, dict):
            continue
        raw = page.get("file")
        if isinstance(raw, str) and raw.strip():
            files.add(Path(raw.strip()).name)
        if page.get("type") == "cover_pdf":
            keys.add("cover")
        for field in ("page", "slot_id"):
            key = page.get(field)
            if isinstance(key, str) and key.strip():
                keys.add(key.strip())
    return files, keys


def undeclared_plan_pages(config_name: str) -> list[str]:
    config = CONFIGS / config_name
    manifest = ROOT / load_config_mapping(config)["paths"]["page_manifest"]
    files, keys = declared_names(manifest)
    plan = json.loads(configs_with_a_plan()[config_name].read_text(encoding="utf-8"))
    missing: list[str] = []
    for page in plan["pages"]:
        ref = str(page["source_ref"])
        stem = Path(ref).stem
        if Path(ref).name in files:
            continue
        if any(stem == key or stem.startswith(key + "_") or key in stem for key in keys):
            continue
        missing.append(ref)
    return missing


class EveryFrozenPlanIsPinned(unittest.TestCase):
    def test_every_configured_plan_has_a_pin(self) -> None:
        self.assertEqual(
            sorted(PINNED_UNDECLARED),
            sorted(configs_with_a_plan()),
            "a config gained or lost a target_assembly plan; add or remove its "
            "pin above, and say in the comment whether the new target builds "
            "from its own source",
        )

    def test_no_target_has_undeclared_plan_pages_beyond_its_pin(self) -> None:
        for config_name, pinned in sorted(PINNED_UNDECLARED.items()):
            with self.subTest(config=config_name):
                self.assertEqual(
                    list(pinned),
                    undeclared_plan_pages(config_name),
                    f"{config_name}: the set of plan pages its manifest cannot "
                    "produce changed. More pages means this target no longer "
                    "builds from its own source; fewer means the debt was paid "
                    "-- shrink the pin.",
                )

    def test_the_pin_is_not_vacuous(self) -> None:
        # Guard against the whole check passing because discovery found nothing.
        self.assertGreaterEqual(len(configs_with_a_plan()), 4)
        self.assertTrue(any(PINNED_UNDECLARED.values()))
        self.assertTrue(any(pin == () for pin in PINNED_UNDECLARED.values()))


class TheDetectorFires(unittest.TestCase):
    def test_a_plan_page_no_manifest_declares_is_reported(self) -> None:
        # BP@JP is fully declared today; planting one unknown page must surface.
        real = undeclared_plan_pages("config.bp-jp.yaml")
        self.assertEqual([], real)

        manifest = ROOT / load_config_mapping(
            CONFIGS / "config.bp-jp.yaml"
        )["paths"]["page_manifest"]
        files, keys = declared_names(manifest)
        planted = "page/a_page_nobody_declares.rst"
        stem = Path(planted).stem
        self.assertNotIn(Path(planted).name, files)
        self.assertFalse(
            any(stem == key or stem.startswith(key + "_") or key in stem for key in keys)
        )


if __name__ == "__main__":
    unittest.main()
