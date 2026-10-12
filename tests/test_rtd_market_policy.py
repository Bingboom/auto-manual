"""Keep policy evidence and its verification status tied to the same snapshot."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.rtd.market_policy import market_context


class MarketPolicyTests(unittest.TestCase):
    def snapshot(self, folder, *, status="verified", sources=None, **fields):
        record = dict.fromkeys(("title", "country", "region", "timeline", "change",
                               "mechanism", "impact", "boundary", "reviewed"), "example")
        record.update(id="example-policy", status=status, tags=["example"], sources=sources or [])
        record.update(fields)
        content = Path(folder, "market-policy")
        content.mkdir(exist_ok=True)
        (content / "records.json").write_text(json.dumps({
            "schema_version": 1, "reviewed": "2026-10-06", "records": [record],
        }), encoding="utf-8")
        return content

    def test_missing_snapshot_is_empty(self):
        with TemporaryDirectory() as folder:
            self.assertEqual(market_context(Path(folder))["records"], [])

    def test_verified_record_needs_official_evidence(self):
        with TemporaryDirectory() as folder:
            self.snapshot(folder, sources=[{"kind": "brief", "url": "https://example.org/brief"}])
            with self.assertRaisesRegex(ValueError, "official source"):
                market_context(Path(folder))
            self.snapshot(folder, sources=[{"kind": "official", "url": "https://example.org/policy"}])
            self.assertEqual(market_context(Path(folder))["records"][0]["status"], "verified")

    def test_unsafe_source_links_block_the_build(self):
        for url in ("javascript:alert(1)", "http://example.org", "https://user:password@example.org"):
            with self.subTest(url=url), TemporaryDirectory() as folder:
                self.snapshot(folder, sources=[{"kind": "official", "url": url}])
                with self.assertRaisesRegex(ValueError, "HTTPS URL"):
                    market_context(Path(folder))

    def test_source_image_cannot_escape_its_business_directory(self):
        with TemporaryDirectory() as folder:
            content = self.snapshot(folder, status="unverified", image="../evidence.jpg")
            content.joinpath("evidence.jpg").write_bytes(b"original evidence")
            with self.assertRaisesRegex(ValueError, "unsafe policy source image"):
                market_context(Path(folder))
            self.snapshot(folder, status="unverified", image="evidence.jpg")
            content.joinpath("_assets").mkdir()
            content.joinpath("_assets", "evidence.jpg").symlink_to(content / "evidence.jpg")
            with self.assertRaisesRegex(ValueError, "unsafe policy source image"):
                market_context(Path(folder))

    def test_recorded_business_basis_does_not_claim_policy_verification(self):
        for status in ("demand", "unverified"):
            with self.subTest(status=status), TemporaryDirectory() as folder:
                self.snapshot(folder, status=status, evidence_note="Operator recorded this requirement.")
                record = market_context(Path(folder))["records"][0]
                self.assertEqual(record["status"], status)
                self.assertEqual(record["sources"], [])
        with TemporaryDirectory() as folder:
            self.snapshot(folder, evidence_note="Operator recorded this requirement.")
            with self.assertRaisesRegex(ValueError, "tags and evidence"):
                market_context(Path(folder))


if __name__ == "__main__":
    unittest.main()
