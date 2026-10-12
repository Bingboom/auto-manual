from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.rtd import system_data
from tools.rtd.system_data import (
    SystemDataError, read_assets, read_published, read_targets, review_page_counts, system_data_context,
    system_data_page_context,
)
from tools.utils.path_utils import Paths, repo_root

CAPABILITIES = "Document_key,Project,UPS功能,静音充电\nJE-A_EU,P1,TRUE,FALSE\nJE-A_US,P1,TRUE,TRUE\nJE-B_JP,P2,FALSE,FALSE\n"
LANGUAGES = "Document_key,Project,languages,notes\nJE-A_EU,P1,en;fr,note\n"
ASSETS = (
    "asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,导出物路径,语言变体,内容哈希,备注\n"
    "a1,,插图,按语言,✅成品,FALSE,JE-A,EU,p,en,h,\n"
    "a2,,图标,中立,⛔隔离,FALSE,ALL,ALL,p,,h,\n"
    "a3,,插图,按语言,🔧临时替代,FALSE,JE-B,JP,p,ja,h,\n"
)


def manifest(path: Path, targets: list[dict]) -> Path:
    path.write_text(json.dumps({"built_at": "2026-10-09T01:00:00+00:00", "targets": targets}), encoding="utf-8")
    return path


def target(model: str, region: str, lang: str, built_at: str = "2026-10-01T00:00:00+00:00") -> dict:
    return {"model": model, "region": region, "lang": lang, "route": f"{model}/{region}/{lang}/md",
            "manual": f"manual_{lang}.md", "version": "1.0", "built_at": built_at}


class SystemDataTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.paths = Paths(self.root)
        self.paths.data_dir.mkdir()
        (self.paths.data_dir / "model_capabilities.csv").write_text(CAPABILITIES, encoding="utf-8")
        (self.paths.data_dir / "model_languages.csv").write_text(LANGUAGES, encoding="utf-8")
        (self.paths.data_dir / "asset_registry.csv").write_text(ASSETS, encoding="utf-8")
        page_dir = self.paths.review_dir / "JE-A" / "EU" / "page"
        page_dir.mkdir(parents=True)
        for name in ("a.rst", "b.rst"):
            (page_dir / name).write_text("x", encoding="utf-8")
        self.manifest = manifest(self.root / "publish_manifest.json", [
            target("JE-A", "EU", "en"), target("JE-A", "EU", "fr", "2026-10-05T00:00:00+00:00"), target("JE-B", "JP", "ja"),
        ])

    def context(self, manifest_path: Path | None = None):
        return system_data_context(self.root, manifest_path or self.manifest, {"en": "English", "ja": "日本語"})

    def test_counts_and_rows_come_from_the_repository_files(self):
        context = self.context()
        self.assertEqual(context["summary"], {
            "manuals": 3, "models": 2, "languages": 3, "regions": 2, "targets": 3,
            "review_targets": 1, "assets": 3, "ready_share": "33.3%",
        })
        self.assertEqual(context["built_on"], "2026-10-09")
        # Newest build first, each row linked to its manual page.
        self.assertEqual([row["lang"] for row in context["published"]], ["fr", "ja", "en"])
        self.assertEqual(context["published"][0]["docname"], "JE-A/EU/fr/md/manual_fr")
        self.assertEqual([region["code"] for region in context["regions"]], ["EU", "JP", "US"])
        self.assertEqual(context["models"], ["JE-A", "JE-B"])
        payload = json.loads(context["data_json"])
        self.assertEqual(payload["capabilities"], ["UPS功能", "静音充电"])
        self.assertEqual(payload["targets"][0], {
            "key": "JE-A_EU", "model": "JE-A", "region": "EU", "project": "P1", "caps": [1, 0],
            "langs": ["en", "fr"], "review_pages": 2,
        })
        self.assertEqual(payload["published"][0], {"model": "JE-A", "region": "EU", "lang": "fr"})
        self.assertEqual(payload["assets"][1], {"category": "图标", "status": "隔离", "model": "ALL", "region": "ALL"})
        self.assertEqual(payload["language_labels"], {"en": "English", "ja": "日本語"})

    def test_a_missing_manifest_leaves_only_the_publication_cards_empty(self):
        context = self.context(self.root / "missing.json")
        self.assertIsNone(context["published"])
        self.assertIsNone(context["summary"]["manuals"])
        self.assertEqual(context["summary"]["targets"], 3)
        self.assertIsNone(json.loads(context["data_json"])["published"])
        self.assertEqual(read_published(self.root / "missing.json"), (None, ""))

    def test_the_json_block_cannot_close_its_script_element(self):
        path = self.paths.data_dir / "model_capabilities.csv"
        path.write_text(CAPABILITIES.replace("P2", "</script><b>"), encoding="utf-8")
        data_json = self.context()["data_json"]
        self.assertNotIn("<", data_json)
        self.assertEqual(json.loads(data_json)["targets"][2]["project"], "</script><b>")

    def test_malformed_data_fails(self):
        cases = {
            "model_capabilities.csv": [
                CAPABILITIES.replace("JE-B_JP,P2,FALSE", "JE-B_JP,P2,yes"),
                CAPABILITIES.replace("JE-B_JP", "JE-B"),
                "Document_key,Project\nJE-A_EU,P1\n",
                "Document_key,UPS功能\nJE-A_EU,TRUE\n",
            ],
            "asset_registry.csv": [
                ASSETS.replace(",JE-B,JP,", ",JE-B,,"),
                "asset_key,类别,状态\na1,插图,✅成品\n",
            ],
        }
        for name, texts in cases.items():
            original = (self.paths.data_dir / name).read_text(encoding="utf-8")
            for text in texts:
                with self.subTest(name=name, text=text[:40]):
                    (self.paths.data_dir / name).write_text(text, encoding="utf-8")
                    with self.assertRaises(SystemDataError):
                        self.context()
            (self.paths.data_dir / name).write_text(original, encoding="utf-8")

    def test_the_page_drops_out_with_a_warning_on_drifted_data(self):
        (self.paths.data_dir / "model_capabilities.csv").write_text("Document_key\nJE-A_EU\n", encoding="utf-8")
        app = SimpleNamespace(srcdir=str(self.root / "web"))
        with patch.object(system_data, "repo_root", return_value=self.root), \
                patch("sphinx.util.logging.getLogger") as get_logger:
            self.assertIsNone(system_data_page_context(app, {}))
        get_logger.return_value.warning.assert_called_once()
        self.assertIn("System data page skipped", get_logger.return_value.warning.call_args.args[0])

    def test_review_pages_are_counted_per_model_and_region(self):
        self.assertEqual(dict(review_page_counts(self.paths.review_dir)), {"JE-A_EU": 2})
        self.assertEqual(dict(review_page_counts(self.root / "nowhere")), {})

    def test_the_committed_repository_data_is_readable(self):
        paths = Paths(repo_root())
        names, targets = read_targets(
            paths.data_dir / "model_capabilities.csv", paths.data_dir / "model_languages.csv", paths.review_dir,
        )
        self.assertTrue(names)
        self.assertTrue(all(len(row["caps"]) == len(names) for row in targets))
        statuses = {row["status"] for row in read_assets(paths.data_dir / "asset_registry.csv")}
        self.assertIn("成品", statuses)
        self.assertFalse(any(status[:1] in "✅⛔🔧❌" for status in statuses))


if __name__ == "__main__":
    unittest.main()
