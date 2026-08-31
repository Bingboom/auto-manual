from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.target_defaults import discover_target_defaults


class TestTargetDefaults(unittest.TestCase):
    def test_repository_scan_preserves_legacy_compatibility_surfaces(self) -> None:
        defaults = discover_target_defaults()

        self.assertEqual(
            {
                "en": "configs/config.us-en.yaml",
                "es": "configs/config.us-es.yaml",
                "fr": "configs/config.us-fr.yaml",
            },
            defaults.us_single_language_target_configs,
        )
        self.assertEqual(
            {
                "en": "configs/config.us-en.yaml",
                "es": "configs/config.us-es.yaml",
                "fr": "configs/config.us-fr.yaml",
                "ja": "configs/config.ja.yaml",
            },
            defaults.language_batch_target_configs,
        )
        self.assertEqual(
            (
                "configs/config.us-en.yaml",
                "configs/config.us-es.yaml",
                "configs/config.us-fr.yaml",
                "configs/config.ja.yaml",
                "configs/config.zh.yaml",
            ),
            defaults.review_workspace_target_configs,
        )
        self.assertEqual(
            {
                "US": "configs/config.us.yaml",
                "EU": "configs/config.eu.yaml",
                "JP": "configs/config.ja.yaml",
                "CN": "configs/config.zh.yaml",
                "KR": "configs/config.kr.yaml",
            },
            defaults.family_default_configs,
        )

    def test_scan_adds_new_us_single_language_config_without_code_edit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            configs_dir = Path(td)
            self._write_config(
                configs_dir / "config.us.yaml",
                region="US",
                languages="en, fr",
                queue_by_document_key=True,
            )
            for language in ("en", "es", "fr", "de"):
                self._write_config(
                    configs_dir / f"config.us-{language}.yaml",
                    region="US",
                    languages=language,
                    include_lang=True,
                )
            self._write_config(
                configs_dir / "config.ja.yaml",
                region="JP",
                languages="ja",
            )
            self._write_config(configs_dir / "config.zh.yaml", region="CN", languages="zh")
            self._write_config(
                configs_dir / "config.kr.yaml",
                region="KR",
                languages="ko",
                include_lang=True,
            )
            self._write_config(
                configs_dir / "config.eu.yaml",
                region="EU",
                languages="en, fr",
                queue_by_document_key=True,
            )

            defaults = discover_target_defaults(configs_dir)

        self.assertEqual(
            {
                "de": "config.us-de.yaml",
                "en": "config.us-en.yaml",
                "es": "config.us-es.yaml",
                "fr": "config.us-fr.yaml",
            },
            {language: Path(path).name for language, path in defaults.us_single_language_target_configs.items()},
        )
        self.assertEqual(
            {
                "de": "config.us-de.yaml",
                "en": "config.us-en.yaml",
                "es": "config.us-es.yaml",
                "fr": "config.us-fr.yaml",
                "ja": "config.ja.yaml",
            },
            {language: Path(path).name for language, path in defaults.language_batch_target_configs.items()},
        )

    @staticmethod
    def _write_config(
        path: Path,
        *,
        region: str,
        languages: str,
        include_lang: bool = False,
        queue_by_document_key: bool = False,
        family_default: bool = False,
    ) -> None:
        path.write_text(
            "build:\n"
            f"  default_region: {region}\n"
            f"  languages: [{languages}]\n"
            f"  include_lang_in_output_path: {'true' if include_lang else 'false'}\n"
            f"  queue_by_document_key: {'true' if queue_by_document_key else 'false'}\n"
            f"  family_default: {'true' if family_default else 'false'}\n",
            encoding="utf-8",
        )

    def test_explicit_main_jp_default_closes_both_bp_jp_ambiguity_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            configs_dir = Path(td)
            self._write_config(
                configs_dir / "config.ja.yaml",
                region="JP",
                languages="ja",
                family_default=True,
            )
            self._write_config(
                configs_dir / "config.bp-jp.yaml",
                region="JP",
                languages="ja",
                queue_by_document_key=True,
            )
            self._write_config(
                configs_dir / "config.us.yaml",
                region="US",
                languages="en, fr",
            )
            self._write_config(
                configs_dir / "config.us-en.yaml",
                region="US",
                languages="en",
                include_lang=True,
            )
            self._write_config(
                configs_dir / "config.eu.yaml",
                region="EU",
                languages="en, fr",
            )
            self._write_config(
                configs_dir / "config.zh.yaml", region="CN", languages="zh"
            )
            self._write_config(
                configs_dir / "config.kr.yaml", region="KR", languages="ko"
            )

            defaults = discover_target_defaults(configs_dir)

        self.assertEqual("config.ja.yaml", Path(defaults.family_default_configs["JP"]).name)
        self.assertEqual(
            "config.ja.yaml",
            Path(defaults.language_batch_target_configs["ja"]).name,
        )

    def test_duplicate_single_language_configs_without_explicit_default_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            configs_dir = Path(td)
            for path, region, languages in (
                ("config.us.yaml", "US", "en"),
                ("config.eu.yaml", "EU", "en"),
                ("config.ja.yaml", "JP", "ja"),
                ("config.bp-jp.yaml", "JP", "ja"),
                ("config.zh.yaml", "CN", "zh"),
                ("config.kr.yaml", "KR", "ko"),
            ):
                self._write_config(
                    configs_dir / path,
                    region=region,
                    languages=languages,
                    # Let config.bp-jp win the family score so this fixture
                    # reaches the separate single-language ambiguity path.
                    queue_by_document_key=path == "config.bp-jp.yaml",
                )

            with self.assertRaisesRegex(RuntimeError, "without exactly one explicit"):
                discover_target_defaults(configs_dir)


class RepositoryConfigScanTests(unittest.TestCase):
    def test_us_family_default_survives_the_bp_config(self) -> None:
        # Skeleton-library slice S1 guard: with configs/config.bp-us.yaml
        # present (same region, same language count), the US family default
        # must stay config.us.yaml — the JP experiment showed a near-tie can
        # silently swap the whole family default. Runs against the real
        # configs/ directory, so a future config addition that flips the
        # default turns this red instead of shipping.
        from tools.target_defaults import discover_target_defaults

        defaults = discover_target_defaults()
        self.assertEqual(
            "configs/config.us.yaml",
            defaults.family_default_configs["US"],
        )


if __name__ == "__main__":
    unittest.main()
