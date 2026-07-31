from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FAKE_LANGUAGE_PROBE = r'''
from dataclasses import replace
from importlib import import_module, reload

from tools import lang_registry


def _xx_columns(columns):
    output = []
    for column in columns:
        prefix, separator, suffix = column.rpartition("_")
        output.append(f"{prefix}_xx" if separator and suffix == "en" else column)
    return tuple(output)


english = lang_registry.language_spec("en")
assert english is not None
fake = replace(
    english,
    code="xx",
    aliases=("xx",),
    column_suffixes=("xx",),
    table_columns=(
        ("spec_master", ("Row_label_xx", "Param_xx", "Value_xx")),
        *(
            (table, _xx_columns(columns))
            for table, columns in english.table_columns
        ),
    ),
    tm_column="xx",
    localized_copy_column="text_xx",
    status_word_column="xx",
    spec_title_column="title_xx",
    display_name="Fake Language",
    template_directory="page_shared/xx",
)

# This is the only fake-language input. No consumer module is patched with an
# xx-specific map; the modules are reloaded exactly as they are at process
# start after one registry row has been added.
lang_registry.LANGUAGE_REGISTRY = (*lang_registry.LANGUAGE_REGISTRY, fake)
lang_registry.LANGUAGE_BY_CODE = {
    spec.code: spec for spec in lang_registry.LANGUAGE_REGISTRY
}
lang_registry.LANGUAGE_BY_ALIAS = {
    alias.casefold(): spec.code
    for spec in lang_registry.LANGUAGE_REGISTRY
    for alias in spec.aliases
}

manual_copy_source = reload(import_module("tools.manual_copy_source"))
localized_copy = reload(import_module("tools.localized_copy"))
signal_words = reload(import_module("tools.signal_words"))
content_lint_languages = reload(import_module("tools.content_lint_languages"))
queue_query_languages = reload(import_module("tools.queue_query_languages"))
sync_data_models = reload(import_module("tools.sync_data_models"))
preview_render = reload(import_module("tools.process_docs.build_review_preview_render"))

assert lang_registry.canonical_language("xx") == "xx"
assert lang_registry.language_alias_candidates("xx") == ("xx",)
assert lang_registry.table_language_columns("spec_master")[-3:] == (
    "Row_label_xx", "Param_xx", "Value_xx"
)

schema_columns = sync_data_models.TABLE_SCHEMAS["symbols_blocks"].columns
xx_start = schema_columns.index("label_xx")
assert schema_columns[xx_start : xx_start + 3] == (
    "label_xx", "aliases_xx", "text_xx"
)
assert "text_xx" in manual_copy_source.LOCALIZED_COPY_COLUMNS
assert manual_copy_source.TM_LANGUAGE_FIELDS["xx"] == "xx"
assert "xx" in manual_copy_source.STATUS_WORD_COLUMNS
assert localized_copy._LANG_TEXT_COLUMNS["xx"] == "text_xx"
assert "xx" in signal_words._SUPPORTED_LANGS
assert "label_xx" in signal_words._label_columns("xx")
assert "xx" in content_lint_languages.SUPPORTED_LANGS
assert content_lint_languages._TEXT["xx"] == "xx"
assert queue_query_languages.canonical_query_lang("xx") == "xx"
assert "xx" in queue_query_languages.SUPPORTED_LANGS
assert preview_render.preview_language_label("xx") == "Fake Language"

resolver = localized_copy.LocalizedCopyResolver(
    [{"copy_key": "fake.key", "text_xx": "Fake copy"}]
)
assert resolver.resolve("fake.key", lang="xx") == "Fake copy"
assert signal_words.labels_from_signal_row(
    {"symbol_key": "warning", "label_xx": "Fake warning"},
    lang="xx",
) == ("Fake warning", "WARNING")

# A normal output language is not an approved reference-bound IDML language.
# Registering it must not silently opt it into a physical layout contract.
assert "xx" not in lang_registry.governed_languages()
assert lang_registry.idml_language_pack("xx") is None
'''


class FakeLanguageEndToEndTest(unittest.TestCase):
    def test_fake_language_registry_row_reaches_all_consumers(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(FAKE_LANGUAGE_PROBE)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"fake-language probe failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
