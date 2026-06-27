from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.local_env import (
    ENV_FILE_OVERRIDE,
    load_local_env_file,
    parse_env_file,
)

SAMPLE = """\
# phase2 source base
export FEISHU_PHASE2_BASE_TOKEN=DOp8bczA8aGLhJsc5iMcOqOvnpg

export FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID=tblTw54UzV4ry5VD
PLAIN_NO_EXPORT=plainvalue
QUOTED="quoted value"
SINGLE='single value'
# a comment line
malformed line without equals
=missing_key
export FEISHU_TRANSLATION_MEMORY_BASE_TOKEN=LUIcbxeKdaCY2rsEHwCcnVQSnUe
"""


class ParseEnvFileTests(unittest.TestCase):
    def test_parses_export_plain_and_quoted(self) -> None:
        parsed = parse_env_file(SAMPLE)
        self.assertEqual(parsed["FEISHU_PHASE2_BASE_TOKEN"], "DOp8bczA8aGLhJsc5iMcOqOvnpg")
        self.assertEqual(parsed["FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID"], "tblTw54UzV4ry5VD")
        self.assertEqual(parsed["PLAIN_NO_EXPORT"], "plainvalue")
        self.assertEqual(parsed["QUOTED"], "quoted value")
        self.assertEqual(parsed["SINGLE"], "single value")
        self.assertEqual(
            parsed["FEISHU_TRANSLATION_MEMORY_BASE_TOKEN"],
            "LUIcbxeKdaCY2rsEHwCcnVQSnUe",
        )

    def test_skips_comments_blanks_and_malformed(self) -> None:
        parsed = parse_env_file(SAMPLE)
        self.assertNotIn("malformed line without equals", parsed)
        self.assertNotIn("", parsed)
        # No bogus key produced by the `=missing_key` line.
        self.assertEqual(len(parsed), 6)


class LoadLocalEnvFileTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".env", delete=False, encoding="utf-8")
        tmp.write(text)
        tmp.close()
        path = Path(tmp.name)
        self.addCleanup(path.unlink)
        return path

    def test_loads_into_environ(self) -> None:
        path = self._write(SAMPLE)
        env: dict[str, str] = {}
        applied = load_local_env_file(path, environ=env)
        self.assertIn("FEISHU_PHASE2_BASE_TOKEN", applied)
        self.assertEqual(env["FEISHU_PHASE2_BASE_TOKEN"], "DOp8bczA8aGLhJsc5iMcOqOvnpg")
        self.assertEqual(env["FEISHU_TRANSLATION_MEMORY_BASE_TOKEN"], "LUIcbxeKdaCY2rsEHwCcnVQSnUe")

    def test_does_not_override_existing_nonempty(self) -> None:
        path = self._write(SAMPLE)
        env = {"FEISHU_PHASE2_BASE_TOKEN": "already-set"}
        applied = load_local_env_file(path, environ=env)
        self.assertEqual(env["FEISHU_PHASE2_BASE_TOKEN"], "already-set")
        self.assertNotIn("FEISHU_PHASE2_BASE_TOKEN", applied)

    def test_fills_existing_empty_value(self) -> None:
        path = self._write(SAMPLE)
        env = {"FEISHU_PHASE2_BASE_TOKEN": "   "}
        applied = load_local_env_file(path, environ=env)
        self.assertEqual(env["FEISHU_PHASE2_BASE_TOKEN"], "DOp8bczA8aGLhJsc5iMcOqOvnpg")
        self.assertIn("FEISHU_PHASE2_BASE_TOKEN", applied)

    def test_override_true_replaces_existing(self) -> None:
        path = self._write(SAMPLE)
        env = {"FEISHU_PHASE2_BASE_TOKEN": "already-set"}
        load_local_env_file(path, environ=env, override=True)
        self.assertEqual(env["FEISHU_PHASE2_BASE_TOKEN"], "DOp8bczA8aGLhJsc5iMcOqOvnpg")

    def test_missing_file_is_noop(self) -> None:
        env: dict[str, str] = {}
        applied = load_local_env_file(Path("/no/such/auto-manual-phase2.env"), environ=env)
        self.assertEqual(applied, [])
        self.assertEqual(env, {})

    def test_override_path_env_var(self) -> None:
        path = self._write("export FOO_BAR=baz\n")
        env = {ENV_FILE_OVERRIDE: str(path)}
        applied = load_local_env_file(environ=env)
        self.assertIn("FOO_BAR", applied)
        self.assertEqual(env["FOO_BAR"], "baz")


if __name__ == "__main__":
    unittest.main()
