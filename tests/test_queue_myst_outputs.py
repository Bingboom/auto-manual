from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.build_docs import render_build_template, resolve_output_path
from tools.queue_outputs import resolve_myst_output_path_for_target


def _build_root_for_target(
    model: str,
    region: str,
    lang: str | None = None,
    *,
    docs_build_dir: Path,
) -> Path:
    parts = [docs_build_dir, Path(model), Path(region)]
    if lang:
        parts.append(Path(lang))
    return Path(*parts)


class QueueMystOutputTests(unittest.TestCase):
    def test_resolve_myst_output_path_should_fall_back_to_word_name_with_md_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us.yaml"
            cfg = {
                "build": {
                    "languages": ["en"],
                    "word_output": "manual_{model_slug}_{region_slug}_{lang}.docx",
                }
            }

            path = resolve_myst_output_path_for_target(
                config_path=config_path,
                model="JE-1000F",
                region="US",
                repo_root=root,
                config_loader=lambda _: cfg,
                build_languages=lambda loaded: loaded["build"]["languages"],
                resolve_output_lang=lambda _: "en",
                build_root_for_target=_build_root_for_target,
                render_build_template=render_build_template,
                resolve_output_path=resolve_output_path,
            )

        self.assertEqual(
            root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "myst" / "manual_je1000f_us_en.md",
            path,
        )

    def test_resolve_myst_output_path_should_honor_configured_myst_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us.yaml"
            cfg = {
                "build": {
                    "languages": ["en"],
                    "myst_output": "rtd_{model_slug}_{region_slug}.md",
                    "word_output": "ignored.docx",
                }
            }

            path = resolve_myst_output_path_for_target(
                config_path=config_path,
                model="JE-1000F",
                region="US",
                repo_root=root,
                config_loader=lambda _: cfg,
                build_languages=lambda loaded: loaded["build"]["languages"],
                resolve_output_lang=lambda _: None,
                build_root_for_target=_build_root_for_target,
                render_build_template=render_build_template,
                resolve_output_path=resolve_output_path,
            )

        self.assertEqual(
            root / "docs" / "_build" / "JE-1000F" / "US" / "myst" / "rtd_je1000f_us.md",
            path,
        )


if __name__ == "__main__":
    unittest.main()
