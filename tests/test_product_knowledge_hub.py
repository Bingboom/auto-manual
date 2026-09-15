"""Portal input isolation and link-only public metadata checks."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'prototypes/product-knowledge-hub/build_portal.py'
spec = importlib.util.spec_from_file_location('hub_builder', SCRIPT)
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class HubBoundaryTests(unittest.TestCase):
    def test_public_output_excludes_internal_metadata(self):
        with TemporaryDirectory() as directory:
            links = Path(directory) / 'links.json'
            links.write_text(json.dumps({'practices': [
                {'title': 'Internal secret', 'url': 'https://alidocs.dingtalk.com/i/nodes/internal', 'tags': []},
                {'title': 'Vibe Coding', 'url': 'https://alidocs.dingtalk.com/i/nodes/public', 'tags': ['Vibe Coding'], 'visibility': 'public'},
            ]}))
            result = hub.read_practices(links, 'public')
            self.assertEqual([r['title'] for r in result], ['Vibe Coding'])
            self.assertNotIn('Internal secret', json.dumps(result))

    def test_rejects_unsafe_links_and_publish_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            links = root / 'links.json'
            for url in ['javascript:alert(1)', 'https://alidocs.dingtalk.com.evil.test/doc', 'https://user:pass@alidocs.dingtalk.com/doc']:
                links.write_text(json.dumps({'practices': [{'title': 'Test', 'url': url}]}))
                with self.assertRaises(ValueError):
                    hub.read_practices(links, 'internal')
            with self.assertRaises(ValueError):
                hub.build(root, root / 'portal', 'https://example.com/', links, 'internal')
