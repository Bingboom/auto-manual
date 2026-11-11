"""Historical input fixtures stay exact and do not hide source mutations."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tests.historical_web_inputs import historical_inputs, historical_repository_inputs
from tools.web.presentation import load_web_manual_contract
from tools.manual_ir.hashing import file_sha256


class HistoricalWebInputTests(unittest.TestCase):
    def test_target_contract_cache_does_not_cross_historical_contexts(self):
        current = load_web_manual_contract(model="JS-100I", region="EU")
        with historical_repository_inputs():
            historical = load_web_manual_contract(model="JS-100I", region="EU")
        self.assertNotEqual(current["warranty"], historical["warranty"])
        self.assertEqual(current, load_web_manual_contract(model="JS-100I", region="EU"))

    def test_historical_dependencies_are_scoped_and_same_for_text_and_bytes(self):
        inputs = historical_inputs()
        before = {path: path.read_bytes() for path in inputs}
        with historical_repository_inputs():
            for path, data in inputs.items():
                self.assertEqual(data, path.read_bytes())
                self.assertEqual(data.decode("utf-8"), path.read_text(encoding="utf-8"))
                self.assertEqual(hashlib.sha256(data).hexdigest(), file_sha256(path))
        self.assertEqual(before, {path: path.read_bytes() for path in inputs})

    def test_temporary_source_mutations_are_never_shadowed(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.json"
            source.write_text("original", encoding="utf-8")
            with historical_repository_inputs():
                source.write_text("changed", encoding="utf-8")
                self.assertEqual(b"changed", source.read_bytes())
                self.assertEqual("changed", source.read_text(encoding="utf-8"))
