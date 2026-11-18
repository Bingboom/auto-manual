"""产品演进时间轴 (tools/rtd/product_timeline.py): synthetic-data tests for context building and template output."""
from __future__ import annotations

import json
import unittest

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from tools.rtd import product_timeline as ptl
from tools.rtd.portal import ASSETS


def product(model: str, market: str, *, category: str | None = "便携储能", series: str | None = "标准",
            short_name: str | None = None, capacity_tier: str | None = "1度电",
            first_sku_created: str | None = None, upper_bound: bool = False) -> dict:
    return {
        "key": f"{model}/{market}",
        "model": model,
        "market": market,
        "category": category,
        "series": series,
        "short_name": short_name,
        "capacity_tier": capacity_tier,
        "names": {"en": f"Name {model}"},
        "first_sku_created": first_sku_created,
        "first_sku_created_upper_bound": upper_bound,
    }


SNAPSHOT = {
    "schema": "hello-docs-product-matrix-snapshot/v1.2",
    "read_at": "2026-11-16T02:00:00Z",
    "parameters": [],
    "sources": [],
    "values": [],
    "cells": [{"product": "FAKE-A/US", "parameter": "capacity_wh", "display": "1000 Wh"}],
    "products": [
        product("FAKE-A", "US", series="Pro", short_name="E1000Pro", first_sku_created="2023-10-21", upper_bound=True),
        product("FAKE-A", "JP", series="Pro", short_name="E1000Pro", first_sku_created="2024-02"),
        product("FAKE-B", "EU", category=None, series=None, capacity_tier=None, first_sku_created="2025-08-05"),
        product("../UNSAFE", "US", first_sku_created="2025-01-01"),
    ],
}

CATALOG = {
    "categories": [{"name": "太阳能板", "series": []}, {"name": "便携储能", "series": []}],
    "models": {"FAKE-B": {"category": "太阳能板", "series": "SolarSaga", "short_name": "100W Light"}},
}


def render_page(context: dict) -> BeautifulSoup:
    env = Environment(loader=FileSystemLoader(ASSETS))
    nav = {"system": True, "deliverables": True, "design": True, "matrix": True}
    return BeautifulSoup(
        env.get_template(ptl.TIMELINE_TEMPLATE).render(**context, freshness=None, site_nav=nav,
                                                       pathto=lambda name, *args: name),
        "html.parser",
    )


class TimelineViewTests(unittest.TestCase):
    def test_builds_sorted_markets_and_catalog_fallbacks_for_safe_models_only(self) -> None:
        view = ptl.timeline_view(SNAPSHOT, CATALOG, today="2026-11-18")
        self.assertTrue(view["built"])
        self.assertEqual(view["categories"], ["太阳能板", "便携储能"])
        self.assertEqual(view["default_category"], "便携储能")
        self.assertEqual([m["code"] for m in view["markets"]], ["US", "EU", "JP"])

        data = view["data"]
        self.assertEqual((data["min_year"], data["max_year"], data["today"]), (2023, 2027, "2026-11-18"))
        self.assertTrue(data["has_profiles"])
        models = {item["model"]: item for item in data["products"]}
        self.assertEqual(sorted(models), ["FAKE-A", "FAKE-B"])
        self.assertEqual(models["FAKE-A"]["markets"], [
            {"market": "US", "date": "2023-10-21", "upper": True},
            {"market": "JP", "date": "2024-02-15", "upper": False},
        ])
        self.assertEqual(
            (models["FAKE-B"]["category"], models["FAKE-B"]["series"], models["FAKE-B"]["short_name"]),
            ("太阳能板", "SolarSaga", "100W Light"),
        )

    def test_template_renders_tabs_controls_and_escaped_json(self) -> None:
        nasty = {
            **{k: v for k, v in SNAPSHOT.items() if k != "cells"},
            "products": [product("FAKE-X", "US", short_name="</script><b>X</b>", first_sku_created="2025-06-01")],
        }
        view = ptl.timeline_view(nasty, None, today="2026-11-18")
        self.assertFalse(view["data"]["has_profiles"])
        page = render_page(view)
        self.assertEqual(page.select_one(".pt-tabs .is-on").get_text(), "演进时间轴")
        self.assertTrue(page.select_one("[data-tl]").has_attr("hidden"))
        raw_script = page.select_one("#tl-data").string or ""
        self.assertNotIn("</script>", raw_script)
        parsed = json.loads(raw_script)
        self.assertEqual(parsed["products"][0]["short_name"], "</script><b>X</b>")
        self.assertNotIn("project", raw_script)

    def test_empty_products_and_undated_products_fail_gracefully(self) -> None:
        empty = ptl.timeline_view({"products": []}, CATALOG)
        self.assertEqual((empty["built"], empty["problem"]), (False, ptl.NO_PRODUCTS))
        self.assertEqual(render_page(empty).select_one(".fr-empty").get_text(), ptl.NO_PRODUCTS)

        undated = ptl.timeline_view({"products": [product("FAKE-A", "US", first_sku_created=None)]}, CATALOG)
        self.assertEqual((undated["built"], undated["problem"]), (False, ptl.NO_DATES))
        self.assertEqual(render_page(undated).select_one(".fr-empty").get_text(), ptl.NO_DATES)


if __name__ == "__main__":
    unittest.main()
