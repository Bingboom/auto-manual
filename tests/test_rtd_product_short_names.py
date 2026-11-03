"""Portal search by product short name (商品简称): snapshot, card text, search index."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from jinja2 import Environment, FileSystemLoader

from tools.rtd import portal as rtd_portal
from tools.rtd import portal_search
from tools.rtd.product_short_names import (
    SNAPSHOT, attach_short_names, load_short_names, short_names_from_rows, standard_name,
)

EXCLUDE = ["+", "样机", "定制", "色", "联名"]


class ShortNameSnapshotTests(unittest.TestCase):
    def test_committed_snapshot_loads_with_operator_examples(self):
        names = load_short_names(rtd_portal.ASSETS)
        self.assertEqual(names["JE-300D"], "E300D")
        self.assertEqual(names["JHP-1000A"], "HP1000v2")
        self.assertEqual(names["JE-1500C"], "E1500Ultra")
        self.assertEqual(names["JE-5000A"], "E5000Plus")
        for name in names.values():
            self.assertFalse(any(marker in name for marker in EXCLUDE), name)

    def test_missing_snapshot_is_empty_and_malformed_fails(self):
        with TemporaryDirectory() as temp:
            assets = Path(temp)
            self.assertEqual(load_short_names(assets), {})
            (assets / SNAPSHOT).write_text(json.dumps({"short_names": {"JE-1": ""}}))
            with self.assertRaises(ValueError):
                load_short_names(assets)

    def test_exact_model_match_and_unlisted_models_stay_empty(self):
        products = attach_short_names([{"model": "JE-300D"}, {"model": "JE-300D-X"}], {"JE-300D": "E300D"})
        self.assertEqual([p["short_name"] for p in products], ["E300D", ""])

    def test_refresh_rule_excludes_variants_and_takes_the_majority(self):
        self.assertEqual(standard_name(["E300D"] * 2 + ["E300", "E300D+SolarSaga", "E300D样机"], EXCLUDE)[0],
                         "E300D")
        self.assertEqual(standard_name(["E300 灰色", "E300定制"], EXCLUDE)[0], "")
        rows = [{"客户型号": "JE-240A", "商品简称": n} for n in ("E240V2", "E240V2", "E240")]
        rows.append({"客户型号": [{"text": "JE-240AX"}], "商品简称": "Other"})
        names, ambiguous = short_names_from_rows(rows, ["JE-240A", "JE-NONE"], model_field="客户型号",
                                                 name_field="商品简称", exclude=EXCLUDE)
        self.assertEqual(names, {"JE-240A": "E240V2"})
        self.assertEqual(set(ambiguous), {"JE-240A"})


class ShortNameSearchTests(unittest.TestCase):
    def test_card_search_text_includes_short_name_lowercased(self):
        env = Environment(loader=FileSystemLoader(str(rtd_portal.ASSETS)), autoescape=False)
        source = env.loader.get_source(env, "manual_portal.html")[0]
        macro = source[source.index("{% macro card"):source.index("{% endmacro %}") + len("{% endmacro %}")]
        template = env.from_string(macro + "{{ card(product, 'x') }}")
        product = {"model": "JE-300D", "region": "EU", "category": "Power stations", "name": "Explorer 300D",
                   "short_name": "E300D", "image": "", "url": "u.html", "version": "", "edition": "EUUK",
                   "language_options": [], "language_scope": "legacy"}
        html = template.render(product=product, portal={"regions": {"EU": "EU"}, "default_region": "EU"},
                               pathto=lambda p, *a: p)
        self.assertIn('data-search="explorer 300d je-300d e300d"', html)
        self.assertIn('class="short-name">· E300D</span>', html)
        product["short_name"] = ""
        html = template.render(product=product, portal={"regions": {"EU": "EU"}, "default_region": "EU"},
                               pathto=lambda p, *a: p)
        self.assertNotIn("short-name", html)

    def test_search_index_rows_carry_short_name(self):
        with TemporaryDirectory() as temp:
            out = Path(temp)
            (out / "m.html").write_text('<main><section id="s"><h2>Charging</h2><p>Use AC.</p></section></main>')
            product = {"model": "JHP-1000A", "name": "Explorer 1000", "short_name": "HP1000v2", "region": "US",
                       "category": "Power stations",
                       "publications": [{"url": "m.html", "lang": "en", "language_scope": "single"}]}
            app = SimpleNamespace(outdir=str(out), builder=SimpleNamespace(format="html"))
            with patch("tools.rtd.portal.portal_data", return_value=({"language_labels": {"en": "English"}},
                                                                     [product])):
                portal_search.write_search_index(app, None)
            text = (out / "_static" / "portal-search-index.js").read_text()
            rows = json.loads(text.split("=", 1)[1].rstrip().rstrip(";"))
            self.assertEqual({row["short_name"] for row in rows}, {"HP1000v2"})


if __name__ == "__main__":
    unittest.main()
