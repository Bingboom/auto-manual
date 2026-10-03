"""Production evidence must not turn snapshots or missing inputs into results."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.rtd.production_evidence import (
    NOT_APPLICABLE, NOT_TRACKED, UNAVAILABLE, activity_windows,
    component_references, metric, production_context, production_metrics, read_publications, skeleton_total,
)
from tools.rtd.source_registry import load_registry
from tools.rtd.deliverables import ASSETS, load_snapshot
from tools.utils.path_utils import Paths, repo_root


class ProductionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.source = {"label": "fixture", "date": "2026-10-02", "href": "https://example.org", "sha256": "a" * 64}
        self.target = dict(model="M", region="EU", lang="en", route="M/EU/en/md", manual="manual.md")

    def metrics(self, targets, snapshot):
        return {m["id"]: m for m in production_metrics(targets, snapshot, self.source, self.source)}

    def test_versions_formats_and_retries_do_not_multiply_identity(self):
        targets = [dict(self.target, version="1"), dict(self.target, version="2"), self.target,
                   dict(self.target, lang="de"), dict(self.target, region="US")]
        docs = [dict(self.target, formats={"word": {}, "print": {}}),
                dict(self.target, formats={"word": {}}),
                dict(model="M", region="EU", lang="", formats={"word": {}})]
        results = self.metrics(targets, {"documents": docs})
        self.assertEqual(results["manuals"]["value"], 2)
        for key in ("variants", "targets", "published"):
            self.assertEqual(results[key]["value"], 3)
        self.assertEqual(results["word"]["value"], 2)
        self.assertEqual(results["print"]["value"], 1)
        self.assertEqual(results["idml"]["display"], NOT_TRACKED)
        self.assertEqual(results["pdf"]["display"], NOT_TRACKED)

    def test_unknown_language_does_not_invent_variant(self):
        docs = [dict(model="M", region="EU", lang="", formats={"word": {}})]
        results = self.metrics([], {"documents": docs})
        self.assertEqual(results["targets"]["value"], 0)
        self.assertEqual(results["word"]["value"], 1)

    def test_zero_missing_and_not_applicable_are_distinct(self):
        good = self.metrics([], {"documents": []})
        bad = self.metrics(None, None)
        for key in ("manuals", "variants", "targets", "published", "word", "print"):
            self.assertEqual(good[key]["display"], "0")
            self.assertEqual(bad[key]["display"], UNAVAILABLE)
            self.assertIsNone(bad[key]["value"])
        self.assertEqual(good["manuals"]["denominator"], NOT_APPLICABLE)
        self.assertEqual(metric("x", "x", None, unit="x", rule="x", sources=[], state=NOT_APPLICABLE)["display"], NOT_APPLICABLE)

    def test_empty_catalog_vs_unreadable_or_partial_identity(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            self.assertIsNone(read_publications(path)[0])
            for payload in ({}, {"targets": {}}, {"targets": [42]}, {"targets": [{"model": "M"}]}):
                path.write_text(json.dumps(payload))
                self.assertIsNone(read_publications(path)[0])
            path.write_text('{"targets": []}')
            self.assertEqual(read_publications(path), ([], ""))
            path.write_text('{broken')
            self.assertIsNone(read_publications(path)[0])

    def test_production_union_includes_known_unpublished_delivery_targets(self):
        docs = [dict(model="Other", region="JP", lang="ja", formats={"word": {}})]
        results = self.metrics([self.target], {"documents": docs})
        self.assertEqual(results["targets"]["value"], 2)
        self.assertEqual(results["published"]["value"], 1)
        self.assertEqual(self.metrics([self.target], None)["targets"]["display"], UNAVAILABLE)

    def test_actual_instance_inheritance_yields_explicit_reference_targets(self):
        refs, total = component_references(Paths(root=repo_root()))
        self.assertGreater(total, 0)
        ids = {(r["component"], r["model"], r["region"]) for r in refs}
        self.assertEqual(len(ids), len(refs))
        self.assertIn(("HB-SPECIAL-OVERVIEW", "JE-1000F", "EU"), ids)
        self.assertFalse(any("lang" in ref for ref in refs))
        with TemporaryDirectory() as temp:
            self.assertEqual(component_references(Paths(root=Path(temp))), (None, None))

    def test_skeleton_copies_do_not_add_assets_and_missing_identity_is_not_a_filename(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            from tools.utils.path_utils import skeletons_of
            directory = skeletons_of(root)
            directory.mkdir(parents=True)
            self.assertEqual(skeleton_total(root), 0)
            for name in ("original", "renamed-copy"):
                path = directory / name / "blueprint.yaml"
                path.parent.mkdir()
                path.write_text("schema_version: skeleton-blueprint/v1\nskeleton_id: same\n")
            self.assertEqual(skeleton_total(root), 1)
            path.write_text("schema_version: skeleton-blueprint/v1\n")
            self.assertIsNone(skeleton_total(root))

    def test_windows_are_utc_half_open_and_not_snapshot_events(self):
        windows = activity_windows(dt.date(2026, 10, 2))
        self.assertEqual([(w["start"], w["end"]) for w in windows],
                         [("2026-09-25", "2026-10-02"), ("2026-09-02", "2026-10-02")])
        self.assertIn("Build Retries", windows[0]["metrics"])
        self.assertIn("Repeat Publications", windows[0]["metrics"])

    def test_context_exposes_staleness_missing_inputs_and_source_provenance(self):
        registry, _ = load_registry(ASSETS)
        snapshot, _ = load_snapshot(ASSETS / registry["deliverables_feishu"]["snapshot"])
        with TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            context = production_context(root=repo_root(), assets=ASSETS, manifest=path, snapshot=snapshot,
                                         registry=registry, today=dt.date(2027, 1, 1), delivery_stale=["交付快照已过期"])
        self.assertIn("交付快照已过期", context["alerts"])
        self.assertTrue(any("发布目录 Unavailable" in alert for alert in context["alerts"]))
        self.assertTrue(any("语料快照" in alert for alert in context["alerts"]))
        for item in context["overview"] + context["assets"] + [context["reference_metric"]]:
            for key in ("scope", "rule", "unit", "denominator", "sources", "guide"):
                self.assertIn(key, item)
            for source in item["sources"]:
                self.assertTrue(source["href"].startswith("https://"))
                self.assertTrue(source["date"])
                self.assertTrue(source["sha256"])


if __name__ == "__main__":
    unittest.main()
