"""The product pages' data freshness (tools/rtd/product_freshness.py, product_freshness in _product_tabs.html).

Judged at build time from the committed snapshot and status.json, without the base. Every model and project here
is invented (FAKE-*, P-FAKE-*).
"""
from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.product_matrix_base.sync import STATUS_SCHEMA
from tools.rtd import portal
from tools.rtd import product_freshness as pf
from tools.rtd import product_library as pl
from tools.rtd import product_tables, product_timeline
from tools.rtd.portal import ASSETS
from tools.rtd.source_registry import load_registry

TODAY = dt.date(2026, 11, 18)
OLD = {"schema": "hello-docs-product-matrix-snapshot/v1.1", "read_at": "2026-11-16T02:00:00Z",
       "products": [{"key": "FAKE-1/US", "model": "FAKE-1", "market": "US", "project": "P-FAKE-1"}]}
NEW = {**OLD, "schema": "hello-docs-product-matrix-snapshot/v1.2", "built_at": "2026-11-16T02:00:09Z",
       "source_modified_at": "2026-11-15T01:00:00Z"}


def status(state="current", **fields):
    value = {"schema": STATUS_SCHEMA, "kind": "product_matrix", "status": state, "checked_at": "2026-11-17T23:17:00Z",
             "last_success": "2026-11-17T23:17:00Z", "snapshot": {"read_at": NEW["read_at"]},
             "source": {"source_modified_at": NEW["source_modified_at"]}, "lag": {"behind": False, "reason": ""}}
    return {**value, **fields}


def render(template: str, context: dict) -> BeautifulSoup:
    html = Environment(loader=FileSystemLoader(ASSETS)).get_template(template).render(
        **context, site_nav={}, pathto=lambda name, *args: name)
    return BeautifulSoup(html, "html.parser")


class FreshnessTest(unittest.TestCase):
    def test_a_v1_1_snapshot_shows_its_read_time_and_an_unknown_build_time(self):
        view = pf.freshness(OLD, None, today=TODAY, limit=7)
        self.assertEqual((view["read_at"], view["built_at"], view["last_success"], view["warnings"]),
                         ("2026-11-16 10:00", pf.UNKNOWN_BUILD, pf.NO_SUCCESS, []))

    def test_a_current_check_is_the_last_success_and_keeps_an_old_read_fresh(self):
        old_read = {**NEW, "read_at": "2026-10-01T00:00:00Z"}
        aged = pf.freshness(old_read, None, today=TODAY, limit=7)
        self.assertEqual(aged["warnings"], ["已超过 7 天没有确认与飞书一致（最近确认 2026-10-01）"])
        confirmed = pf.freshness(old_read, status(snapshot={"read_at": old_read["read_at"]}), today=TODAY, limit=7)
        self.assertEqual((confirmed["warnings"], confirmed["last_success"], confirmed["built_at"]),
                         ([], "2026-11-18 07:17", "2026-11-16 10:00"))

    def test_behind_failed_and_newer_records_warn(self):
        behind = pf.freshness(NEW, status("behind", lag={"behind": True, "reason": "产品 2→3"}), today=TODAY, limit=7)
        self.assertEqual(behind["warnings"], ["飞书已有更新，页面数据落后（检查于 2026-11-18 07:17）：产品 2→3"])
        failed = pf.freshness(NEW, status("failed", last_success="2026-11-16T02:00:00Z"), today=TODAY, limit=7)
        self.assertEqual(failed["warnings"], ["最近一次同步检查失败（2026-11-18 07:17），页面沿用上次成功的数据"])
        self.assertEqual(failed["last_success"], "2026-11-16 10:00")
        newer = pf.freshness(NEW, status(source={"source_modified_at": "2026-11-17T00:00:00Z"}), today=TODAY, limit=7)
        self.assertEqual(newer["warnings"], ["飞书有更晚的事实记录（2026-11-17 08:00），快照还没有包含"])

    def test_a_status_about_another_snapshot_is_ignored(self):
        other = status("behind", snapshot={"read_at": "2026-11-01T00:00:00Z"})
        self.assertEqual(pf.freshness(NEW, other, today=TODAY, limit=7)["warnings"], [])
        self.assertEqual(pf.freshness(NEW, other, today=TODAY, limit=7)["last_success"], pf.NO_SUCCESS)

    def test_the_limit_comes_from_the_source_registry(self):
        registry, problems = load_registry(ASSETS)
        self.assertEqual(problems, [])
        self.assertEqual(pf.stale_limit(registry), registry["product_matrix"]["stale_after_days"])
        self.assertEqual(pf.stale_limit(None), pf.DEFAULT_LIMIT)

    def test_status_is_read_beside_the_snapshot_and_only_with_its_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pl.snapshot_path(Path(tmp)).parent
            folder.mkdir(parents=True)
            self.assertIsNone(pf.freshness_context(Path(tmp), None, today=TODAY, registry=None))
            (folder / "status.json").write_text(json.dumps(status("failed")), encoding="utf-8")
            self.assertEqual(pf.load_status(Path(tmp))["status"], "failed")
            (folder / "status.json").write_text(json.dumps({**status(), "schema": "other/v1"}), encoding="utf-8")
            self.assertIsNone(pf.load_status(Path(tmp)))


class TemplateTest(unittest.TestCase):
    def test_every_product_page_shows_the_times_and_the_warning(self):
        fresh = pf.freshness(NEW, status("behind", lag={"behind": True, "reason": "<b>产品 2→3</b>"}), today=TODAY,
                             limit=7)
        matrix = {**pl.library_view(NEW), "freshness": fresh}
        snapshot = {**NEW, "parameters": [], "cells": []}
        pages = {"product_matrix.html": matrix,
                 "product_timeline.html": {**product_timeline.timeline_view(snapshot, None), "freshness": fresh},
                 "product_table.html": {**product_tables.table_view(snapshot, None), "freshness": fresh},
                 "product_compare.html": {**product_tables.compare_view(snapshot), "freshness": fresh}}
        for template, context in pages.items():
            with self.subTest(template):
                page = render(template, context)
                self.assertEqual([span.get_text() for span in page.select(".pt-sync span")],
                                 ["数据读取于 2026-11-16 10:00", "快照生成于 2026-11-16 10:00",
                                  "最近同步成功 2026-11-18 07:17"])
                banner = page.select_one(".pt-stale")
                self.assertEqual(banner["role"], "status")
                self.assertIn("产品 2→3", banner.li.get_text())
                self.assertIsNone(banner.select_one("b"))  # status text is escaped
        quiet = render("product_matrix.html", {**pl.library_view(NEW), "freshness": pf.freshness(
            NEW, status(), today=TODAY, limit=7)})
        self.assertIsNone(quiet.select_one(".pt-stale"))
        self.assertEqual(quiet.select_one(".fr-head p").get_text(), "1 款产品 · 更新于 2026-11-16")
        empty = render("product_matrix.html", {**pl.empty_context("还没有产品数据。"), "freshness": None})
        self.assertIsNone(empty.select_one(".pt-sync, .pt-stale"))


class PortalTest(unittest.TestCase):
    def test_the_portal_reads_the_status_with_the_configured_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pl.snapshot_path(Path(tmp)).parent
            folder.mkdir(parents=True)
            (folder / "snapshot.json").write_text(json.dumps(NEW), encoding="utf-8")
            (folder / "status.json").write_text(json.dumps(status("failed")), encoding="utf-8")
            app = SimpleNamespace(config=SimpleNamespace(rtd_knowledge_dir=tmp, rtd_system_workspace_date="2026-12-31"))
            view = portal.product_freshness(app)
        self.assertEqual(len(view["warnings"]), 2)  # failed, and past the limit on the configured date
        self.assertIs(portal.product_freshness(app), view)  # once per build


if __name__ == "__main__":
    unittest.main()
