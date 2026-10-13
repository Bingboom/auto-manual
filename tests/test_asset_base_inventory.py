from __future__ import annotations

import csv
import hashlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from tools.asset_pipeline.base_inventory import (
    IllustrationUse,
    InventoryError,
    art_roots,
    build_inventory,
    check_output_dir,
    derived_web_key,
    folder_locale,
    main,
    registry_sync_preview,
)
from tools.asset_pipeline.base_reconcile import SnapshotError, cell_text, load_snapshot
from tools.asset_registry import APPROVED_STATUS, load_registry
from tools.utils.path_utils import repo_root

ROOT = repo_root()
PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360f8cf00000301010018dd8db40000000049454e44ae426082"
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_snapshot(directory: Path, tables: dict[str, list[tuple[str, dict]]]) -> Path:
    """One lark-cli record-list page per table: field names, positional rows and record ids."""
    directory.mkdir(parents=True, exist_ok=True)
    for table, records in tables.items():
        names = sorted({name for _record_id, fields in records for name in fields})
        page = {"ok": True, "data": {"fields": names, "record_id_list": [record_id for record_id, _ in records],
                                     "data": [[fields.get(name) for name in names] for _, fields in records],
                                     "has_more": False}}
        (directory / f"{table}_records_0.json").write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
    return directory


def _use(language: str, model: str = "JE-1000H", region: str = "EU") -> IllustrationUse:
    return IllustrationUse(manifest=f"m_{language}.json", model=model, region=region, language=language,
                           sha256="", source_key="", source_sha256="", source_name="", source_page="",
                           source_crop="", replaces=())


class RepositoryInventoryTests(unittest.TestCase):
    """Invariants of the dry run over the real tree."""

    @classmethod
    def setUpClass(cls):
        cls.inventory = build_inventory(ROOT)
        cls.exports = {row["repo_path"]: row for row in cls.inventory.exports}
        cls.records = load_registry(ROOT / "data" / "asset_registry.csv")
        cls.approved_keys = {record.asset_key for record in cls.records if record.status == APPROVED_STATUS}

    def test_every_tracked_art_file_is_one_export_with_its_own_bytes(self):
        names = [root.path.relative_to(ROOT).as_posix() for root in art_roots(ROOT)]
        listed = subprocess.run(["git", "-c", "core.quotePath=false", "ls-files", "-z", "--", *names],
                                cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\0")
        art = {name for name in listed if name and Path(name).suffix.lower() in
               {".png", ".svg", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"}}
        self.assertEqual(set(self.exports), art)
        self.assertEqual(len({row["export_key"] for row in self.inventory.exports}), len(self.inventory.exports))
        for repo_path in sorted(art)[::25]:
            data = (ROOT / repo_path).read_bytes()
            with self.subTest(file=repo_path):
                self.assertEqual(self.exports[repo_path]["content_sha256"], _sha(data))
                self.assertEqual(int(self.exports[repo_path]["size_bytes"]), len(data))

    def test_registry_facts_flow_into_definitions_unchanged(self):
        definitions = self.inventory.definitions
        for row in self.inventory.exports:
            self.assertIn(row["asset_key"], definitions, row["repo_path"])
        for record in self.records:
            with self.subTest(asset=record.asset_key):
                definition = definitions[record.asset_key]
                self.assertEqual(definition["status"], record.status)
                self.assertEqual(definition["category"], record.category)
                self.assertEqual(definition["language_dimension"], record.language_dimension)
                self.assertEqual(definition["needs_review"], "FALSE")

    def test_shared_manifests_name_their_files_but_only_the_registry_approves(self):
        shared = ROOT / "docs" / "renderers" / "web" / "assets" / "shared"
        symbols = json.loads((shared / "symbols" / "manifest.json").read_text(encoding="utf-8"))
        buttons = json.loads((shared / "buttons" / "manifest.json").read_text(encoding="utf-8"))
        named = [(shared / "symbols" / asset["path"], asset["key"]) for asset in symbols["assets"]]
        named += [(shared / "buttons" / asset["asset"], asset["semantic_key"]) for asset in buttons["assets"]]
        for path, key in named:
            row = self.exports[path.relative_to(ROOT).as_posix()]
            with self.subTest(asset=key):
                self.assertEqual((row["asset_key"], row["artifact_kind"]), (key, "web-shared"))
                self.assertEqual(row["gate_status"], "approved" if key in self.approved_keys else "pending")
        withdrawn = {item["sha256"] for item in symbols["withdrawn"]}
        self.assertTrue(withdrawn)
        for row in self.inventory.exports:
            if row["content_sha256"] in withdrawn:
                self.assertIn("网页符号清单已撤回这份位图", row["notes"], row["repo_path"])
                self.assertNotIn(row["artifact_kind"], {"web-shared", "web-target"})

    def test_gates_and_review_flags_agree(self):
        for row in self.inventory.exports:
            with self.subTest(file=row["repo_path"]):
                self.assertIn(row["gate_status"], {"approved", "pending", "quarantine", "temporary", "missing"})
                self.assertEqual(row["build_eligible"], "TRUE" if row["gate_status"] == "approved" else "FALSE")
                self.assertEqual(row["visual_review_required"],
                                 "FALSE" if row["gate_status"] == "approved" else "TRUE")
                if row["gate_status"] == "approved":
                    self.assertIn(row["asset_key"], self.approved_keys)
                if row["registered_in"] == "" or row["gate_status"] == "pending":
                    self.assertEqual(row["needs_review"], "TRUE")

    def test_staging_the_registry_definitions_would_leave_the_registry_unchanged(self):
        preview = registry_sync_preview(self.inventory, ROOT)
        self.assertEqual(preview["registered_definitions"],
                         {"rows": len(self.records), "registry_unchanged": True, "changed_keys": []})
        proposed = preview["proposed_definitions"]
        self.assertEqual(proposed["would_append"], proposed["rows"])
        self.assertEqual(proposed["without_status"], proposed["rows"])
        self.assertIn("unknown status", proposed["registry_loader"])


class DerivedKeyTests(unittest.TestCase):
    def test_a_registered_folder_lends_its_prefix_and_separator(self):
        conventions = {"docs/renderers/web/assets/je1000h_eu_de": ("web/je1000h/eu/de", "_"),
                       "docs/renderers/web/assets/ja_ad01a_eu_en": ("web/ja-ad01a/eu/en", "-")}
        self.assertEqual(derived_web_key("docs/renderers/web/assets/je1000h_eu_de/charging-solar.png",
                                         (_use("de"),), conventions), "web/je1000h/eu/de/charging_solar")
        self.assertEqual(derived_web_key("docs/renderers/web/assets/ja_ad01a_eu_en/inbox_cable.png",
                                         (_use("en", "JA-AD01A"),), conventions), "web/ja-ad01a/eu/en/inbox-cable")

    def test_otherwise_the_majority_spelling_applies(self):
        path = "docs/renderers/web/assets/je2000e_eu_nl/Battery_Pack.png"
        self.assertEqual(derived_web_key(path, (_use("nl", "JE-2000E"),), {}), "web/je2000e/eu/nl/battery_pack")
        self.assertEqual(derived_web_key(path, (_use("nl", "JE-2000E"), _use("pt", "JE-2000E")), {}),
                         "web/je2000e/eu/shared/battery_pack")
        self.assertEqual(derived_web_key("docs/renderers/web/assets/je100c_eu_shared/lcd1.svg", (), {}),
                         "web/je100c-eu-shared/lcd1")


class FolderLocaleTests(unittest.TestCase):
    def test_the_language_follows_the_region_in_a_per_target_folder_name(self):
        regions = frozenset({"eu", "us", "jp", "kr"})
        cases = (("je1000h_eu_uk", "uk"), ("je1000e_sil_us_en", "en"), ("ja_ts05a_us_shared", "shared"),
                 ("je3000c_eu_de_20260915", "de"), ("je2000f_eu_en_full_frames", "en"), ("jbp2000b_jp", ""),
                 ("js100i_eu_added", ""), ("je100c_kr_ko", "ko"))
        for folder, locale in cases:
            with self.subTest(folder=folder):
                self.assertEqual(folder_locale(folder, regions), locale)


class FixtureInventoryTests(unittest.TestCase):
    """The resolution order and the findings, on a tree small enough to read."""

    REGISTRY_HEADER = ("asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,"
                       "导出物路径,语言变体,内容哈希,备注\n")

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.web = self.root / "docs" / "renderers" / "web"
        self.files: dict[str, bytes] = {}

    def tearDown(self):
        self.temp.cleanup()

    def put(self, relative: str, data: bytes) -> str:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.files[relative] = data
        return _sha(data)

    def build_tree(self, *, declared_sha: str | None = None, extra_registry: str = "") -> None:
        symbol = self.put("docs/renderers/web/assets/shared/symbols/native-v1/symbol_weee.svg", b"<svg/>")
        withdrawn = self.put("docs/templates/word_template/common_assets/symbols/weee.png", PNG_1x1 + b"w")
        self.put("docs/renderers/web/assets/shared/lcd/lcd_parallel.png", PNG_1x1 + b"l")
        art = self.put("docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png", PNG_1x1 + b"b")
        self.put("docs/renderers/web/assets/je2000e_eu_nl/stray_copy.png", PNG_1x1 + b"w")
        temporary = self.put("docs/renderers/latex/assets/placeholder.png", PNG_1x1 + b"t")
        self.put("docs/renderers/web/assets/shared/symbols/manifest.json", json.dumps({
            "schema_version": "auto-manual-shared-web-symbols/v1",
            "assets": [{"key": "weee/crossed-bin-bar", "path": "native-v1/symbol_weee.svg", "sha256": symbol}],
            "withdrawn": [{"path": "docs/templates/word_template/common_assets/symbols/weee.png",
                           "sha256": withdrawn, "reason": "legacy raster"}],
        }).encode())
        self.put("docs/renderers/web/assets/shared/buttons/manifest.json", json.dumps({"assets": []}).encode())
        self.put("docs/renderers/web/je2000e_eu_nl_illustrations.json", json.dumps({
            "model": "JE-2000E", "region": "EU", "language": "nl", "recipe": "data/asset_recipes/je2000e_nl.json",
            "illustrations": [{"path": "assets/je2000e_eu_nl/battery_pack.png", "sha256": declared_sha or art,
                               "source_page": 7, "bbox_pt": [1, 2, 3, 4], "replaces": ["battery_pack.png"]}],
        }).encode())
        self.put("data/asset_recipes/je2000e_nl.json", json.dumps(
            {"source": {"source_key": "source/je2000e_nl_master", "expected_sha256": "ab" * 32,
                        "expected_page_count": 30}}).encode())
        self.put("data/asset_sources.csv", "source_key,source_kind,sha256,source_pointer\n".encode())
        self.put("data/asset_registry.csv", (
            self.REGISTRY_HEADER
            + "symbols/weee,,图标,中立,✅成品,FALSE,ALL,ALL,"
              f"docs/templates/word_template/common_assets/symbols,,weee.png:{withdrawn},\n"
            + f"placeholder/slot,,插图,中立,🔧临时替代,FALSE,ALL,ALL,docs/renderers/latex/assets,,"
              f"placeholder.png:{temporary},\n"
            + extra_registry).encode("utf-8"))

    def test_identities_gates_and_findings(self):
        # An unmaterialized row is enough to teach the dry run that "fr" is a language code.
        self.build_tree(extra_registry="mark/fr_only,,标记,按语言,✅成品,FALSE,ALL,EU,,fr,,\n")
        self.put("docs/renderers/web/assets/je2000e_eu_added/views_fr.png", PNG_1x1 + b"v")
        inventory = build_inventory(self.root, tracked_only=False)
        exports = {row["repo_path"]: row for row in inventory.exports}
        shared = exports["docs/renderers/web/assets/shared/symbols/native-v1/symbol_weee.svg"]
        self.assertEqual((shared["asset_key"], shared["gate_status"], shared["locale"], shared["needs_review"]),
                         ("weee/crossed-bin-bar", "pending", "shared", "TRUE"))
        legacy = exports["docs/templates/word_template/common_assets/symbols/weee.png"]
        self.assertEqual((legacy["asset_key"], legacy["gate_status"], legacy["notes"]),
                         ("symbols/weee", "approved", "网页符号清单已撤回这份位图：legacy raster"))
        target = exports["docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png"]
        self.assertEqual((target["gate_status"], target["build_eligible"]), ("pending", "FALSE"))
        self.assertEqual((target["asset_key"], target["source_key"], target["source_page"], target["source_crop"]),
                         ("web/je2000e/eu/nl/battery_pack", "source/je2000e_nl_master", "7", "1 2 3 4"))
        self.assertEqual((target["needs_review"], target["pixel_size"], target["has_alpha"]), ("TRUE", "1x1", "TRUE"))
        self.assertEqual(exports["docs/renderers/latex/assets/placeholder.png"]["gate_status"], "temporary")
        self.assertEqual(exports["docs/renderers/web/assets/shared/lcd/lcd_parallel.png"]["asset_key"],
                         "lcd/shared/parallel")
        added = exports["docs/renderers/web/assets/je2000e_eu_added/views_fr.png"]
        self.assertEqual((added["asset_key"], added["locale"]), ("web/je2000e-eu-added/views_fr", "fr"))
        self.assertEqual(inventory.definitions["web/je2000e-eu-added/views_fr"]["language_dimension"], "按语言")
        definition = inventory.definitions["web/je2000e/eu/nl/battery_pack"]
        self.assertEqual((definition["category"], definition["language_dimension"], definition["needs_review"]),
                         ("插图", "按语言", "TRUE"))
        kinds = {(item["kind"], item["subject"]) for item in inventory.findings}
        self.assertIn(("unregistered-file", "docs/renderers/web/assets/shared/lcd/lcd_parallel.png"), kinds)
        self.assertIn(("withdrawn-copy", "docs/renderers/web/assets/je2000e_eu_nl/stray_copy.png"), kinds)
        self.assertIn(("unregistered-master", "source/je2000e_nl_master"), kinds)
        master = inventory.sources["source/je2000e_nl_master"]
        self.assertEqual(master["archive_status"], "待校验")
        self.assertEqual((master["needs_review"], master["source_sha256"], master["page_count"]),
                         ("TRUE", "ab" * 32, "30"))

    def test_registry_rows_name_files_by_path_not_by_bytes(self):
        lockup = _sha(PNG_1x1 + b"k")
        row = "{key},,标记,中立,✅成品,FALSE,ALL,ALL,docs/renderers/latex/assets,,{label}:{sha},\n"
        self.build_tree(extra_registry="".join(row.format(key=key, label=label, sha=lockup) for key, label in (
            ("mark/lockup", "lockup.png"), ("placeholder/lockup_copy", "lockup_copy.png"),
            ("print/lockup_alias", "lockup.png"))))
        self.put("docs/renderers/latex/assets/lockup.png", PNG_1x1 + b"k")
        self.put("docs/renderers/latex/assets/lockup_copy.png", PNG_1x1 + b"k")
        inventory = build_inventory(self.root, tracked_only=False)
        exports = {row["repo_path"]: row for row in inventory.exports}
        lockup_row = exports["docs/renderers/latex/assets/lockup.png"]
        self.assertEqual(exports["docs/renderers/latex/assets/lockup_copy.png"]["asset_key"], "placeholder/lockup_copy")
        self.assertEqual((lockup_row["asset_key"], lockup_row["needs_review"]), ("mark/lockup", "TRUE"))
        self.assertIn("print/lockup_alias", lockup_row["notes"])
        ambiguous = [item["subject"] for item in inventory.findings if item["kind"] == "ambiguous-registry"]
        self.assertEqual(ambiguous, ["docs/renderers/latex/assets/lockup.png"])

    def test_a_byte_copy_in_a_rows_folder_takes_the_rows_key_and_is_reported(self):
        # The v2 label resolves into the LaTeX folder; Word keeps the same bytes under its own name.
        fan = _sha(PNG_1x1 + b"f")
        self.build_tree(extra_registry="operation/fan,,插图,中立,✅成品,FALSE,ALL,ALL,"
                                       f"docs/templates/word_template/common_assets/operation,,v2-png:{fan},\n")
        self.put("docs/renderers/latex/assets/op_fan.png", PNG_1x1 + b"f")
        self.put("docs/templates/word_template/common_assets/operation/fan.png", PNG_1x1 + b"f")
        self.put("docs/renderers/web/assets/je2000e_eu_nl/fan.png", PNG_1x1 + b"f")
        inventory = build_inventory(self.root, tracked_only=False)
        exports = {row["repo_path"]: row for row in inventory.exports}
        self.assertEqual(exports["docs/renderers/latex/assets/op_fan.png"]["needs_review"], "FALSE")
        word = exports["docs/templates/word_template/common_assets/operation/fan.png"]
        self.assertEqual((word["asset_key"], word["gate_status"], word["needs_review"]),
                         ("operation/fan", "approved", "TRUE"))
        self.assertIn("docs/renderers/latex/assets/op_fan.png", word["notes"])
        self.assertNotEqual(exports["docs/renderers/web/assets/je2000e_eu_nl/fan.png"]["asset_key"], "operation/fan")
        copies = [item["subject"] for item in inventory.findings if item["kind"] == "registry-copy"]
        self.assertEqual(copies, ["docs/templates/word_template/common_assets/operation/fan.png"])

    def test_a_registry_hash_that_disagrees_with_the_file_is_reported(self):
        self.build_tree(extra_registry="mark/stale,,标记,中立,✅成品,FALSE,ALL,ALL,docs/renderers/latex/assets,,"
                                       f"stale.png:{'0' * 64},\n")
        self.put("docs/renderers/latex/assets/stale.png", PNG_1x1 + b"s")
        inventory = build_inventory(self.root, tracked_only=False)
        exports = {row["repo_path"]: row for row in inventory.exports}
        self.assertEqual(exports["docs/renderers/latex/assets/stale.png"]["asset_key"], "mark/stale")
        self.assertIn(("hash-mismatch", "docs/renderers/latex/assets/stale.png"),
                      {(item["kind"], item["subject"]) for item in inventory.findings})

    def test_a_manifest_hash_that_disagrees_with_the_file_is_reported(self):
        self.build_tree(declared_sha="0" * 64)
        inventory = build_inventory(self.root, tracked_only=False)
        mismatches = [item for item in inventory.findings if item["kind"] == "hash-mismatch"]
        self.assertEqual([item["subject"] for item in mismatches],
                         ["docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png"])

    def test_the_cli_writes_review_files_and_refuses_repository_folders(self):
        self.build_tree()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        output = self.root.parent / f"{self.root.name}-staging"
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(main(["--repo-root", str(self.root), "--output-dir", str(output)]), 0)
                self.assertEqual(main(["--repo-root", str(self.root), "--output-dir", str(self.root / "docs" / "x")]),
                                 2)
            self.assertIn("refusing to write staging files inside docs/", stderr.getvalue())
            with (output / "asset_exports.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["repo_path"] for row in rows},
                             {path for path in self.files if Path(path).suffix in {".png", ".svg"}})
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["rows"]["asset_exports"], len(rows))
            self.assertTrue(summary["registry_sync_preview"]["registered_definitions"]["registry_unchanged"])
        finally:
            for path in sorted(output.glob("*")):
                path.unlink()
            output.rmdir()

    def live_snapshot(self, *, placeholder_sha: str = "0" * 64) -> Path:
        art = _sha(PNG_1x1 + b"b")
        weee = "docs/templates/word_template/common_assets/symbols/weee.png"
        # Outside the four art folders, so the dry run does not stage the snapshot itself.
        return write_snapshot(self.root / "live-snapshot", {
            "sources": [("recS1", {"source_key": "source/je2000e_nl_master"})],
            "definitions": [
                ("recD1", {"asset_key": "symbols/weee", "category": "标记", "language_dimension": ["中立"],
                           "status": ["✅成品"], "textless_pending": False, "model_scope": "ALL",
                           "region_scope": "ALL",
                           "language_variants": None}),
                ("recD2", {"asset_key": "web/je2000e/eu/nl/battery-pack", "category": "插图",
                           "language_dimension": ["按语言"], "status": ["✅成品"], "model_scope": "JE-2000E",
                           "region_scope": "EU", "language_variants": "nl"}),
                ("recD3", {"asset_key": "mark/base_only", "category": "标记", "language_dimension": ["中立"],
                           "status": ["✅成品"], "model_scope": "ALL", "region_scope": "ALL"}),
            ],
            "exports": [
                ("recE1", {"export_key": "registry::docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png",
                           "repo_path": "docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png",
                           "asset_key": "web/je2000e/eu/nl/battery-pack", "content_sha256": art, "像素尺寸": "1x1",
                           "export_file": [{"file_token": "tok1", "name": "battery_pack.png", "size": 70}]}),
                ("recE2", {"export_key": "registry::docs/renderers/latex/assets/placeholder.png",
                           "repo_path": "docs/renderers/latex/assets/placeholder.png", "asset_key": "placeholder/slot",
                           "content_sha256": placeholder_sha}),
                ("recE3", {"export_key": "registry::docs/renderers/latex/assets/gone.png",
                           "repo_path": "docs/renderers/latex/assets/gone.png", "asset_key": "placeholder/slot",
                           "content_sha256": "1" * 64}),
                ("recE4", {"export_key": "source/x::artifacts/weee.png", "artifact_kind": ["semantic-export"],
                           "repo_path": weee, "asset_key": "symbols/weee", "content_sha256": "2" * 64}),
                ("recE5", {"export_key": "registry::docs/renderers/web/assets/je2000e_eu_nl/stray_copy.png",
                           "repo_path": "docs/renderers/web/assets/je2000e_eu_nl/stray_copy.png",
                           "asset_key": "web/base/stray", "content_sha256": _sha(PNG_1x1 + b"w")}),
            ],
        })

    def test_a_live_snapshot_gives_each_row_its_action_and_the_bases_own_keys(self):
        self.build_tree()
        inventory = build_inventory(self.root, tracked_only=False, live=load_snapshot(self.live_snapshot()))
        exports = {row["repo_path"]: row for row in inventory.exports}
        target = exports["docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png"]
        # The Base already names the file and approves it: its key and status win over the proposal.
        self.assertEqual((target["asset_key"], target["gate_status"], target["action"], target["live_record_id"]),
                         ("web/je2000e/eu/nl/battery-pack", "approved", "fill", "recE1"))
        self.assertIn("artifact_kind", target["fill_fields"].split(";"))
        # 像素尺寸 is already set on the Base row, so pixel_size is not filled again.
        self.assertNotIn("pixel_size", target["fill_fields"].split(";"))
        self.assertEqual(target["needs_review"], "FALSE")
        self.assertEqual(exports["docs/renderers/latex/assets/placeholder.png"]["action"], "update-file")
        self.assertEqual(exports["docs/renderers/web/assets/shared/lcd/lcd_parallel.png"]["action"], "create")
        definitions = inventory.definitions
        self.assertEqual((definitions["web/je2000e/eu/nl/battery-pack"]["key_origin"],
                          definitions["web/je2000e/eu/nl/battery-pack"]["action"]), ("base", "keep"))
        self.assertNotIn("web/je2000e/eu/nl/battery_pack", definitions)
        self.assertEqual(definitions["placeholder/slot"]["action"], "create")
        self.assertEqual(definitions["lcd/shared/parallel"]["action"], "propose")
        # A Base row's key without a Base definition is taken, but stays a proposal.
        stray = exports["docs/renderers/web/assets/je2000e_eu_nl/stray_copy.png"]
        self.assertEqual((stray["asset_key"], stray["gate_status"], stray["needs_review"]),
                         ("web/base/stray", "pending", "TRUE"))
        self.assertEqual((definitions["web/base/stray"]["key_origin"], definitions["web/base/stray"]["action"]),
                         ("derived", "propose"))
        self.assertEqual(inventory.sources["source/je2000e_nl_master"]["action"], "keep")
        self.assertEqual(inventory.sources["source/je2000e_nl_master"]["archive_status"], "")
        kinds = {(item["kind"], item["subject"]) for item in inventory.findings}
        for expected in (("live-key", "docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png"),
                         ("stale-attachment", "docs/renderers/latex/assets/placeholder.png"),
                         ("orphan-export", "docs/renderers/latex/assets/gone.png"),
                         ("stale-intake-export", "docs/templates/word_template/common_assets/symbols/weee.png"),
                         ("base-drift", "symbols/weee"), ("base-only-definition", "mark/base_only")):
            self.assertIn(expected, kinds)

    def test_a_proposed_key_another_files_registry_row_uses_stays_pending(self):
        # The registry approves the full frame; the manifest-bound crop of the same name proposes the same key.
        frame = self.put("docs/renderers/web/assets/je2000e_eu_nl_full_frames/battery_pack.png", PNG_1x1 + b"F")
        self.build_tree(extra_registry="web/je2000e/eu/nl/battery_pack,,插图,按语言,✅成品,FALSE,JE-2000E,EU,"
                                       f"docs/renderers/web/assets/je2000e_eu_nl_full_frames,nl,battery_pack.png:{frame},\n")
        crop = "docs/renderers/web/assets/je2000e_eu_nl/battery_pack.png"
        # After the registry definitions are uploaded, the Base holds the same approved definition.
        uploaded = write_snapshot(self.root / "live-snapshot", {"sources": [], "exports": [], "definitions": [
            ("recD1", {"asset_key": "web/je2000e/eu/nl/battery_pack", "category": "插图",
                       "language_dimension": ["按语言"], "status": ["✅成品"], "model_scope": "JE-2000E",
                       "region_scope": "EU", "language_variants": "nl"})]})
        for live in (None, load_snapshot(uploaded)):
            inventory = build_inventory(self.root, tracked_only=False, live=live)
            exports = {row["repo_path"]: row for row in inventory.exports}
            self.assertEqual((exports[crop]["asset_key"], exports[crop]["gate_status"], exports[crop]["needs_review"]),
                             ("web/je2000e/eu/nl/battery_pack", "pending", "TRUE"))
            full_frame = exports["docs/renderers/web/assets/je2000e_eu_nl_full_frames/battery_pack.png"]
            self.assertEqual(full_frame["gate_status"], "approved")
            self.assertIn(("registry-key-elsewhere", crop),
                          {(item["kind"], item["subject"]) for item in inventory.findings})

    def test_the_live_preview_shows_what_the_next_sync_writes_into_the_registry(self):
        self.build_tree()
        live = load_snapshot(self.live_snapshot())
        inventory = build_inventory(self.root, tracked_only=False, live=live)
        preview = registry_sync_preview(inventory, self.root, live)["next_sync_after_upload"]
        # symbols/weee: the Base's category overwrites the registry's; the Base-only keys are appended.
        self.assertEqual(preview["changed_keys"], ["symbols/weee"])
        self.assertEqual(sorted(preview["appended_keys"]), ["mark/base_only", "web/je2000e/eu/nl/battery-pack"])
        self.assertEqual((preview["uploaded_definitions"], preview["registry_loader"]), (1, "ok"))

    def test_a_snapshot_without_a_table_is_refused(self):
        snapshot = write_snapshot(self.root / "partial-snapshot", {"sources": []})
        with self.assertRaisesRegex(SnapshotError, "definitions_records"):
            load_snapshot(snapshot)
        self.assertEqual(cell_text([{"id": "recX"}, {"id": "recY"}]), "recX,recY")
        self.assertEqual(cell_text(["按语言"]), "按语言")
        self.assertEqual(cell_text([{"type": "text", "text": "a, "}, {"type": "text", "text": "b"}]), "a, b")
        self.assertEqual(cell_text(11484.0), "11484")

    def test_output_must_be_new_or_empty(self):
        with TemporaryDirectory() as temp:
            occupied = Path(temp) / "occupied"
            occupied.mkdir()
            (occupied / "old.csv").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(InventoryError, "new or empty"):
                check_output_dir(occupied, self.root)
            check_output_dir(Path(temp) / "fresh", self.root)


if __name__ == "__main__":
    unittest.main()
