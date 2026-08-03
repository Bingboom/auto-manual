from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools import dingtalk_delivery_map as delivery_map
from tools.lang_registry import LANGUAGE_REGISTRY


HEADER = "model,region,lang,project_code,safety_regulation,dingtalk_language,备注\n"


def _write_map(body: str, *, header: str = HEADER) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / delivery_map.DELIVERY_MAP_FILENAME
    path.write_text(header + body, encoding="utf-8")
    return path


class TestDingTalkDeliveryMap(unittest.TestCase):
    def test_repo_map_resolves_known_target(self) -> None:
        target = delivery_map.resolve_delivery_target(model="JE-1000F", region="EU", lang="fr")

        self.assertEqual("HTE153", target.project_code)
        self.assertEqual("欧英规", target.safety_regulation)
        self.assertEqual("法语", target.dingtalk_language)
        self.assertEqual(("HTE153", "欧英规", "法语"), target.dingtalk_identity)
        self.assertEqual(
            {"project_code": "HTE153", "safety_regulation": "欧英规", "language": "法语"},
            target.as_manifest_fields(),
        )

    def test_repo_map_rows_are_internally_consistent(self) -> None:
        targets = delivery_map.load_delivery_map()

        self.assertTrue(targets)
        registered_languages = {spec.code for spec in LANGUAGE_REGISTRY}
        for (model, region, lang), target in targets.items():
            self.assertEqual((model, region, lang), target.repo_key)
            self.assertIn(
                lang,
                registered_languages,
                f"{delivery_map.describe_target(model, region, lang)} uses an unregistered language code",
            )
            self.assertTrue(target.project_code.startswith("HTE"), target.project_code)

    def test_repo_map_pairs_one_safety_regulation_per_region(self) -> None:
        targets = delivery_map.load_delivery_map()

        by_region: dict[tuple[str, str], set[str]] = {}
        for (model, region, _lang), target in targets.items():
            by_region.setdefault((model, region), set()).add(target.safety_regulation)
        for (model, region), regulations in by_region.items():
            self.assertEqual(
                1,
                len(regulations),
                f"model={model} region={region} maps to multiple 安规 values: {sorted(regulations)}",
            )

    def test_unmapped_target_raises_with_actionable_message(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.resolve_delivery_target(model="JE-1000F", region="EU", lang="uk")

        message = str(ctx.exception)
        self.assertIn("no entry for", message)
        self.assertIn("lang=uk", message)
        self.assertIn(delivery_map.DELIVERY_MAP_FILENAME, message)

    def test_duplicate_repo_key_raises(self) -> None:
        path = _write_map(
            "JE-1000F,EU,fr,HTE153,欧英规,法语,\nJE-1000F,EU,fr,HTE153,欧英规,法语,dupe\n"
        )

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("duplicate target", str(ctx.exception))

    def test_missing_column_raises(self) -> None:
        path = _write_map(
            "JE-1000F,EU,fr,HTE153,欧英规\n",
            header="model,region,lang,project_code,safety_regulation\n",
        )

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("missing required column", str(ctx.exception))
        self.assertIn("dingtalk_language", str(ctx.exception))

    def test_blank_required_field_raises(self) -> None:
        path = _write_map("JE-1000F,EU,fr,HTE153,,法语,\n")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("empty required field", str(ctx.exception))
        self.assertIn("safety_regulation", str(ctx.exception))

    def test_blank_lines_are_skipped(self) -> None:
        path = _write_map("JE-1000F,EU,fr,HTE153,欧英规,法语,\n,,,,,,\n")

        targets = delivery_map.load_delivery_map(path)

        self.assertEqual(1, len(targets))

    def test_empty_map_raises(self) -> None:
        path = _write_map("")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("no rows", str(ctx.exception))

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(Path("/nonexistent/dingtalk_delivery_map.csv"))

        self.assertIn("is missing", str(ctx.exception))

    def test_lookup_trims_incoming_values(self) -> None:
        target = delivery_map.resolve_delivery_target(
            model=" JE-1000F ", region=" JP ", lang=" ja "
        )

        self.assertEqual("日规", target.safety_regulation)
        self.assertEqual("日语", target.dingtalk_language)


if __name__ == "__main__":
    unittest.main()
