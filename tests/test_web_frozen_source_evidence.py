from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.web_frozen_source_evidence import (
    SOURCE_SCHEMA, seal_frozen_web_evidence, verify_release_evidence,
)
from tools.web_language_release_evidence import _file_inventory


class FrozenWebEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.md = self.source / 'web' / 'nl'
        self.md.mkdir(parents=True)
        (self.md / 'manual.md').write_text('# Handleiding\n<img src="assets/diagram.png">\n')
        (self.md / 'assets').mkdir()
        (self.md / 'assets' / 'diagram.png').write_bytes(b'figure')
        (self.md / 'conf.py').write_text('extensions = ["myst_parser"]\n')
        (self.md / 'index.md').write_text('# Index\n\n```{toctree}\nmanual\n```\n')
        self.html = self.root / 'html'
        self.html.mkdir()
        (self.html / 'index.html').write_text('<html lang="nl">Handleiding</html>')
        self.manifest = self.source / 'source_manifest.json'
        self.payload = {
            'schema_version': SOURCE_SCHEMA,
            'target': {'model': 'MODEL', 'region': 'EU', 'languages': ['nl'], 'technical_version': 'git-source'},
            'original_source': {'filename': 'source.ai', 'sha256': 'a' * 64},
            'web_roots': {'nl': 'web/nl'},
            'inputs': list(_file_inventory(self.source)),
        }
        self.manifest.write_text(json.dumps(self.payload))

    def seal(self):
        self.receipt = seal_frozen_web_evidence(
            source_manifest_path=self.manifest, source_root=self.source,
            language='nl', markdown_dir=self.md, markdown_name='manual.md',
            html_dir=self.html, evidence_dir=self.root / 'evidence', git_ref='abc123',
        )
        return self.receipt

    def verify(self, **changes):
        args = dict(expected_sha256=hashlib.sha256(self.receipt.read_bytes()).hexdigest(),
                    model='MODEL', region='EU', language='nl', version='git-source',
                    git_ref='abc123', markdown_dir=self.md, markdown_name='manual.md',
                    html_dir=self.html)
        args.update(changes)
        return verify_release_evidence(self.receipt, **args)

    def test_exact_frozen_source_and_stored_copy_verify(self):
        self.seal()
        self.assertEqual(self.verify().language, 'nl')
        stored = self.root / 'stored'
        shutil.copytree(self.md, stored)
        shutil.copytree(self.receipt.parent, stored / 'evidence')
        (stored / 'publish_meta.json').write_text('{}')
        self.receipt = stored / 'evidence' / self.receipt.name
        self.assertEqual(self.verify(markdown_dir=stored, html_dir=None, stored=True).language, 'nl')

    def test_wrong_language_or_release_rejected(self):
        self.seal()
        for fields in ({'language': 'pl'}, {'model': 'OTHER'}, {'version': 'other'}, {'git_ref': 'other'}):
            with self.subTest(fields=fields), self.assertRaisesRegex(RuntimeError, 'identity mismatch'):
                self.verify(**fields)

    def test_missing_or_modified_asset_rejected(self):
        self.seal()
        (self.md / 'assets' / 'diagram.png').unlink()
        with self.assertRaisesRegex(RuntimeError, 'Markdown files differ'):
            self.verify()
        (self.md / 'assets' / 'diagram.png').write_bytes(b'altered')
        with self.assertRaisesRegex(RuntimeError, 'Markdown files differ'):
            self.verify()

    def test_modified_html_and_source_manifest_rejected(self):
        self.seal()
        (self.html / 'index.html').write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'HTML files differ'):
            self.verify()
        (self.receipt.parent / 'frozen_source_manifest.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError, 'manifest SHA-256 mismatch'):
            self.verify()

    def test_detached_markdown_cannot_be_sealed(self):
        (self.md / 'manual.md').write_text('# Changed after review')
        with self.assertRaisesRegex(RuntimeError, 'input files differ'):
            self.seal()

    def test_source_symlink_and_traversal_are_rejected(self):
        (self.md / 'escape').symlink_to(self.html / 'index.html')
        with self.assertRaises(RuntimeError):
            self.seal()
        (self.md / 'escape').unlink()
        self.payload['web_roots']['nl'] = '../escape'
        self.manifest.write_text(json.dumps(self.payload))
        with self.assertRaisesRegex(RuntimeError, 'unsafe'):
            self.seal()

    def test_fresh_verification_requires_html_and_receipt_hash(self):
        self.seal()
        with self.assertRaisesRegex(RuntimeError, 'fresh HTML'):
            self.verify(html_dir=None)
        with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
            self.verify(expected_sha256='f' * 64)

    def test_unpackaged_html_image_rejected_at_seal(self):
        (self.html / 'index.html').write_text('<img src="missing.png">')
        with self.assertRaisesRegex(RuntimeError, 'not a packaged file'):
            self.seal()

    def test_real_assembler_preserves_single_locale_evidence(self):
        from tools.publish_branch_assembly import assemble_web_publish_branch
        releases = self.root / 'reports' / 'releases'
        web = releases / 'MODEL' / 'EU' / 'nl' / 'versions' / 'git-source' / 'web'
        shutil.copytree(self.md, web / 'md')
        shutil.copytree(self.html, web / 'html')
        receipt = seal_frozen_web_evidence(
            source_manifest_path=self.manifest, source_root=self.source,
            language='nl', markdown_dir=web / 'md', markdown_name='manual.md',
            html_dir=web / 'html', evidence_dir=web / 'evidence', git_ref='abc123',
        )
        meta = releases / 'MODEL' / 'EU' / 'nl' / 'latest' / 'web' / 'publish_meta.json'
        meta.parent.mkdir(parents=True)
        meta.write_text(json.dumps({
            'schema_version': 'auto-manual-web-publish/v1',
            'model': 'MODEL', 'region': 'EU', 'lang': 'nl', 'version': 'git-source',
            'git_ref': 'abc123', 'built_at': '2026-09-28T00:00:00Z',
            'md_output_path': str(web / 'md' / 'manual.md'), 'html_dir': str(web / 'html'),
            'language_scope': 'single', 'legacy_default': True,
            'language_projection_evidence_path': str(receipt),
            'language_projection_evidence_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest(),
        }))
        output = self.root / 'candidate' / 'docs' / 'publish'
        assemble_web_publish_branch(repo_root=self.root, releases_root=releases,
                                    output_dir=output, title='Manuals')
        stored = output / 'sources' / 'web' / 'MODEL' / 'EU' / 'nl' / 'md'
        self.assertEqual(json.loads((stored / 'publish_meta.json').read_text())['language_scope'], 'single')
        self.assertTrue((stored / 'evidence' / 'frozen_source_manifest.json').is_file())
        # Reassembling reads and validates the stored evidence, not only fresh inputs.
        assemble_web_publish_branch(repo_root=self.root, releases_root=releases,
                                    output_dir=output, title='Manuals')
