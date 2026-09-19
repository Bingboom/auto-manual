from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools import rtd_deployment_receipt, write_web_publish_html_link
from tools.write_web_publish_html_link import (
    latest_web_publish_metadata,
    persist_rtd_url,
    target_rtd_url,
)


class WriteWebPublishHtmlLinkTests(unittest.TestCase):
    def test_default_base_url_has_a_single_source_of_truth(self) -> None:
        self.assertIs(
            write_web_publish_html_link.DEFAULT_RTD_BASE_URL,
            rtd_deployment_receipt.DEFAULT_RTD_BASE_URL,
        )
        self.assertEqual(
            "ht-doc",
            rtd_deployment_receipt.rtd_project_slug_from_base_url(
                write_web_publish_html_link.DEFAULT_RTD_BASE_URL
            ),
        )

    def test_target_url_is_the_canonical_nested_route(self) -> None:
        # M4 link semantics: HTML_link registers the canonical nested page;
        # the flat root alias stays the printed/QR entry layer.
        url = target_rtd_url(
            base_url="https://ht-doc.readthedocs.io/",
            payload={
                "model": "JE-1000F",
                "region": "US",
                "lang": "en",
                "md_output_path": "reports/releases/JE-1000F/US/en/versions/2.0/web/md/manual_je1000f_us.md",
            },
        )
        self.assertEqual(
            "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html",
            url,
        )

    def test_target_url_requires_language(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "lang"):
            target_rtd_url(
                base_url="https://ht-doc.readthedocs.io",
                payload={
                    "model": "JE-1000F",
                    "region": "US",
                    "md_output_path": "reports/releases/JE-1000F/US/en/versions/2.0/web/md/manual_je1000f_us.md",
                },
            )

    def test_target_url_rejects_unsafe_route_segments(self) -> None:
        with self.assertRaises(ValueError):
            target_rtd_url(
                base_url="https://ht-doc.readthedocs.io",
                payload={
                    "model": "..",
                    "region": "US",
                    "lang": "en",
                    "md_output_path": "reports/releases/JE-1000F/US/en/versions/2.0/web/md/manual_je1000f_us.md",
                },
            )

    def test_pending_mode_persists_url_without_any_bitable_interaction(self) -> None:
        # REV-07: the queue lane only records the deterministic URL as run
        # evidence; the Document_link write belongs to the post-deploy receipt
        # lane. A nonexistent config path proves pending mode never reaches
        # config loading or the lark transport.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            metadata = root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json"
            metadata.parent.mkdir(parents=True)
            payload = {
                "schema_version": "auto-manual-web-publish/v1",
                "model": "JE-1000F",
                "region": "US",
                "lang": "en",
                "md_output_path": "releases/JE-1000F/US/en/versions/2.0/web/md/manual_je1000f_us.md",
                "queue_record_ids": ["rec_pending_1", "rec_pending_2"],
            }
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            deferred = write_web_publish_html_link.write_web_publish_html_links(
                config_path=root / "missing-config.yaml",
                base_url="https://ht-doc.readthedocs.io",
                releases_root=root,
                pending=True,
            )

            self.assertEqual(2, deferred)
            stored = json.loads(metadata.read_text(encoding="utf-8"))
            self.assertEqual(
                "https://ht-doc.readthedocs.io/JE-1000F/US/en/md/manual_je1000f_us.html",
                stored["publish_url"],
            )

    def test_pending_mode_cli_flag_defers_writeback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            metadata = root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json"
            metadata.parent.mkdir(parents=True)
            metadata.write_text(
                json.dumps(
                    {
                        "schema_version": "auto-manual-web-publish/v1",
                        "model": "JE-1000F",
                        "region": "US",
                        "lang": "en",
                        "md_output_path": "releases/x/web/md/manual_je1000f_us.md",
                        "queue_record_ids": ["rec_pending_1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            exit_code = write_web_publish_html_link.main(
                [
                    "--config",
                    str(root / "missing-config.yaml"),
                    "--releases-root",
                    str(root),
                    "--pending",
                ]
            )
            self.assertEqual(0, exit_code)

    def test_latest_metadata_and_persist_should_use_web_subtree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            metadata = root / "JE-1000F" / "US" / "en" / "latest" / "web" / "publish_meta.json"
            metadata.parent.mkdir(parents=True)
            payload = {"schema_version": "auto-manual-web-publish/v1"}
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            self.assertEqual([metadata], latest_web_publish_metadata(root))
            persist_rtd_url(metadata_path=metadata, payload=payload, url="https://example.com/manual.html")
            self.assertEqual(
                "https://example.com/manual.html",
                json.loads(metadata.read_text(encoding="utf-8"))["publish_url"],
            )


if __name__ == "__main__":
    unittest.main()
