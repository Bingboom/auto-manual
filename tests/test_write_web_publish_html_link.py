from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.write_web_publish_html_link import (
    latest_web_publish_metadata,
    persist_rtd_url,
    target_rtd_url,
)


class WriteWebPublishHtmlLinkTests(unittest.TestCase):
    def test_target_url_should_match_readthedocs_short_alias(self) -> None:
        url = target_rtd_url(
            base_url="https://ht-doc.readthedocs.io/",
            payload={
                "model": "JE-1000F",
                "region": "US",
                "md_output_path": "reports/releases/JE-1000F/US/en/versions/2.0/web/md/manual_je1000f_us.md",
            },
        )
        self.assertEqual(
            "https://ht-doc.readthedocs.io/manual_je1000f_us.html",
            url,
        )

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
