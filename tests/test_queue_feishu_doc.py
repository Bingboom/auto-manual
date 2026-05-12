from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.queue_feishu_doc import create_feishu_doc_from_markdown, parse_feishu_doc_create_payload


class QueueFeishuDocTests(unittest.TestCase):
    def test_create_feishu_doc_from_markdown_should_build_docs_create_command(self) -> None:
        calls: list[list[str]] = []

        def fake_run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, object]:
            self.assertEqual("lark-cli", cli_bin)
            calls.append(args)
            return {"data": {"doc_id": "doxcn123", "doc_url": "https://example.feishu.cn/wiki/wikcn123"}}

        with tempfile.TemporaryDirectory() as td:
            markdown_path = Path(td) / "manual.md"
            markdown_path.write_text("# Manual\n", encoding="utf-8")
            result = create_feishu_doc_from_markdown(
                cli_bin="lark-cli",
                identity="user",
                markdown_path=markdown_path,
                destination=SimpleNamespace(parent_wiki_token="wikcn_parent", space_id="spc"),
                title="manual",
                run_lark_cli_json=fake_run_lark_cli_json,
                cli_relative_file_arg=lambda path: "docs/_build/manual.md",
            )

        self.assertEqual("https://example.feishu.cn/wiki/wikcn123", result.document_url)
        self.assertEqual("doxcn123", result.document_id)
        self.assertEqual(
            [
                "docs",
                "+create",
                "--api-version",
                "v2",
                "--as",
                "user",
                "--markdown",
                "@docs/_build/manual.md",
                "--title",
                "manual",
                "--wiki-node",
                "wikcn_parent",
            ],
            calls[0],
        )

    def test_parse_feishu_doc_create_payload_should_accept_nested_cli_shapes(self) -> None:
        result = parse_feishu_doc_create_payload(
            {
                "data": {
                    "document": {
                        "token": "doxcn456",
                        "url": "https://example.feishu.cn/docx/doxcn456",
                    }
                }
            }
        )

        self.assertEqual("doxcn456", result.document_id)
        self.assertEqual("https://example.feishu.cn/docx/doxcn456", result.document_url)


if __name__ == "__main__":
    unittest.main()
