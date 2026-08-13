from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import check_docs


class TestCheckDocsRendererContracts(unittest.TestCase):
    def test_malformed_fcc_fails_check_renderer_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle_dir = Path(td)
            source = bundle_dir / "page" / "01_fcc.rst"
            source.parent.mkdir()
            source.write_text(
                "FCC\n===\n\nThis page has no governed opening line block.\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_fcc_renderer_contract_issues(
                bundle_dir=bundle_dir,
                model="JE-1000F",
                region="US",
                lang="fr",
            )

        self.assertTrue(issues)
        self.assertTrue(all(issue.code == "FCC_RENDER_CONTRACT" for issue in issues))
        self.assertIn("opening line block", issues[0].message)

    def test_pt_br_fcc_passes_document_and_web_preflight(self) -> None:
        template = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "templates"
            / "page_us-pt-br"
            / "01_fcc.rst"
        )
        with tempfile.TemporaryDirectory() as td:
            bundle_dir = Path(td)
            source = bundle_dir / "page" / "01_fcc.rst"
            source.parent.mkdir()
            source.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")

            issues = check_docs.collect_fcc_renderer_contract_issues(
                bundle_dir=bundle_dir,
                model="JE-1500D",
                region="pt-BR",
                lang="pt-BR",
            )

        self.assertEqual([], issues)


if __name__ == "__main__":
    unittest.main()
