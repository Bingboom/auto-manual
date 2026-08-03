from __future__ import annotations

import glob
from pathlib import Path
import tempfile
import unittest

from tools import dingtalk_delivery_map as delivery_map
from tools.config_loader import load_config_mapping


HEADER = "model,region,project_code,safety_regulation,dingtalk_languages,备注\n"


def _write_map(body: str, *, header: str = HEADER) -> Path:
    directory = Path(tempfile.mkdtemp())
    path = directory / delivery_map.DELIVERY_MAP_FILENAME
    path.write_text(header + body, encoding="utf-8")
    return path


def _publishable_targets() -> set[tuple[str, str]]:
    """Whole-book families are the only shapes a publish queue row may use."""

    targets: set[tuple[str, str]] = set()
    for config_path in sorted(glob.glob("configs/config.*.yaml")):
        cfg = load_config_mapping(Path(config_path))
        build = cfg.get("build", cfg)
        if build.get("include_lang_in_output_path", cfg.get("include_lang_in_output_path")):
            continue
        model = build.get("default_model") or cfg.get("default_model")
        region = build.get("default_region") or cfg.get("default_region")
        if model and region:
            targets.add((str(model), str(region)))
    return targets


class TestDingTalkDeliveryMap(unittest.TestCase):
    def test_repo_map_resolves_a_published_region(self) -> None:
        target = delivery_map.resolve_delivery_target(model="JE-1000F", region="EU")

        self.assertEqual("HTE153", target.project_code)
        self.assertEqual("欧英规", target.safety_regulation)
        self.assertEqual(("HTE153", "欧英规"), target.dingtalk_identity)
        self.assertIn("法语", target.dingtalk_languages)
        self.assertEqual(
            {
                "project_code": "HTE153",
                "safety_regulation": "欧英规",
                "languages": list(target.dingtalk_languages),
            },
            target.as_manifest_fields(),
        )

    def test_every_mapped_target_is_publishable(self) -> None:
        """A mapped target the queue can never publish would be dead weight."""

        publishable = _publishable_targets()
        for key in delivery_map.load_delivery_map():
            self.assertIn(
                key,
                publishable,
                f"{delivery_map.describe_target(*key)} is mapped but no whole-book "
                "family can publish it",
            )

    def test_repo_map_rows_are_internally_consistent(self) -> None:
        targets = delivery_map.load_delivery_map()

        self.assertTrue(targets)
        for (model, region), target in targets.items():
            self.assertEqual((model, region), target.repo_key)
            self.assertTrue(target.project_code.startswith("HTE"), target.project_code)
            self.assertTrue(target.dingtalk_languages)
            for language in target.dingtalk_languages:
                self.assertEqual(language, language.strip())

    def test_unmapped_target_raises_not_mapped_not_a_generic_error(self) -> None:
        """Callers must be able to treat "not delivered" as skipped, not failed."""

        with self.assertRaises(delivery_map.DeliveryTargetNotMapped) as ctx:
            delivery_map.resolve_delivery_target(model="JE-2000E", region="CN")

        message = str(ctx.exception)
        self.assertIn("no DingTalk delivery row is mapped", message)
        self.assertIn("region=CN", message)
        self.assertIn(delivery_map.DELIVERY_MAP_FILENAME, message)

    def test_not_mapped_is_not_a_runtime_error(self) -> None:
        self.assertFalse(issubclass(delivery_map.DeliveryTargetNotMapped, RuntimeError))

    def test_languages_split_on_semicolons(self) -> None:
        path = _write_map("JE-1000F,US,HTE153,美加规,英语（美式）;法语;西班牙语,\n")

        target = delivery_map.resolve_delivery_target(
            model="JE-1000F", region="US", path=path
        )

        self.assertEqual(("英语（美式）", "法语", "西班牙语"), target.dingtalk_languages)

    def test_repeated_language_raises(self) -> None:
        path = _write_map("JE-1000F,US,HTE153,美加规,法语;法语,\n")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("repeats a language", str(ctx.exception))

    def test_duplicate_repo_key_raises(self) -> None:
        path = _write_map(
            "JE-1000F,EU,HTE153,欧英规,法语,\nJE-1000F,EU,HTE153,欧英规,德语,dupe\n"
        )

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("duplicate target", str(ctx.exception))

    def test_missing_column_raises(self) -> None:
        path = _write_map(
            "JE-1000F,EU,HTE153,欧英规\n",
            header="model,region,project_code,safety_regulation\n",
        )

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("missing required column", str(ctx.exception))
        self.assertIn("dingtalk_languages", str(ctx.exception))

    def test_blank_required_field_raises(self) -> None:
        path = _write_map("JE-1000F,EU,HTE153,,法语,\n")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_map.load_delivery_map(path)

        self.assertIn("empty required field", str(ctx.exception))
        self.assertIn("safety_regulation", str(ctx.exception))

    def test_blank_lines_are_skipped(self) -> None:
        path = _write_map("JE-1000F,EU,HTE153,欧英规,法语,\n,,,,,\n")

        self.assertEqual(1, len(delivery_map.load_delivery_map(path)))

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
        target = delivery_map.resolve_delivery_target(model=" JE-1000F ", region=" JP ")

        self.assertEqual("日规", target.safety_regulation)
        self.assertEqual(("日语",), target.dingtalk_languages)


if __name__ == "__main__":
    unittest.main()
