"""``tools/intel`` can leave this repository as it is, and agrees with the host where they meet.

The package imports only the standard library and itself (relative imports, so a
move needs no rename), its own tests import only the package, and a copy of both
passes with nothing else from this repository on the path. Where the host keeps a
parallel reader (table pages, policy records) or names a shared route (the
research page), both sides are checked against each other.
"""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools import workspace_snapshot
from tools.intel import cli, feishu
from tools.intel.policies import read_policies
from tools.rtd import market_policy, product_research

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "tools" / "intel"
PACKAGE_TESTS = sorted((ROOT / "tests").glob("test_intel_*.py"))
FIXTURES = ROOT / "tests" / "fixtures" / "external_intel"


def imports(path: Path) -> list[tuple[int, str]]:
    """``(relative level, module)`` of every import statement in ``path``."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [(0, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append((node.level, node.module or ""))
    return found


def outside(path: Path, allowed: str = "") -> list[str]:
    """Imports of ``path`` that are neither relative, standard library nor under ``allowed``."""
    return [module for level, module in imports(path)
            if not level and module.split(".")[0] not in sys.stdlib_module_names
            and not (allowed and (module == allowed or module.startswith(allowed + ".")))]


class BoundaryTests(unittest.TestCase):
    def test_package_imports_only_the_standard_library_and_itself(self):
        modules = sorted(PACKAGE.glob("*.py"))
        self.assertGreaterEqual(len(modules), 8)
        for path in modules:
            with self.subTest(path.name):
                self.assertEqual(outside(path), [])

    def test_package_tests_import_only_the_package(self):
        self.assertGreaterEqual(len(PACKAGE_TESTS), 6)
        for path in PACKAGE_TESTS:
            with self.subTest(path.name):
                self.assertEqual(outside(path, "tools.intel"), [])

    def test_a_copy_passes_its_tests_with_nothing_else_from_this_repository(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(PACKAGE, root / "tools" / "intel", ignore=shutil.ignore_patterns("__pycache__"))
            (root / "tools" / "__init__.py").write_text("", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
            for path in PACKAGE_TESTS:
                shutil.copy2(path, root / "tests" / path.name)
            shutil.copytree(FIXTURES, root / "tests" / "fixtures" / FIXTURES.name)
            # -I keeps PYTHONPATH, the user site and this checkout off the path; discovery adds only the copy.
            result = subprocess.run(
                [sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-p", "test_intel_*.py"],
                cwd=root, capture_output=True, text=True, check=False, timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stderr, r"Ran [1-9]\d* tests")


def page_reader(pages_by_offset):
    def run(args):
        return pages_by_offset[int(args[args.index("--offset") + 1])]
    return run


def page(rows, *, start=0, fields=("a",), more=None, total=None, rev=None, code=0, ids=None):
    data = {"fields": list(fields), "data": rows,
            "record_id_list": ids if ids is not None else [f"rec{start + i}" for i in range(len(rows))]}
    data.update({key: value for key, value in (("has_more", more), ("total", total), ("rev", rev))
                 if value is not None})
    return {"code": code, "data": data}


class HostContractTests(unittest.TestCase):
    def test_table_reads_match_the_host_reader(self):
        full = [[i] for i in range(200)]
        cases = {
            "one page": {0: page([[1], [2]], total=2)},
            "two pages": {0: page(full, more=True, total=230, rev=3), 200: page([[9]] * 30, start=200, more=False,
                                                                                total=230, rev=3)},
            "no total": {0: page([[1]])},
            "error code": {0: page([], code=5)},
            "schema change": {0: page(full, more=True), 200: page([[1]], start=200, fields=("b",))},
            "repeated id": {0: page([[1], [2]], ids=["rec1", "rec1"])},
            "short total": {0: page([[1]], total=4)},
            "bad marker": {0: page([[1]], more="yes")},
            "more after short page": {0: page([[1]], more=True)},
            "total change": {0: page(full, more=True, total=300), 200: page([[1]], start=200, total=301)},
            "revision change": {0: page(full, more=True, rev=1), 200: page([[1]], start=200, rev=2)},
            "long row": {0: page([[1, 2]])},
        }
        for name, pages in cases.items():
            with self.subTest(name):
                outcomes = []
                for reader in (feishu.complete_rows, workspace_snapshot.complete_rows):
                    try:
                        outcomes.append(reader(page_reader(pages), "b", "t"))
                    except RuntimeError:
                        outcomes.append("raised")
                self.assertEqual(outcomes[0], outcomes[1])

    def test_policy_records_read_the_same_as_the_portal(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(read_policies(root), market_policy.market_context(root)["records"])
            (root / "market-policy").mkdir()
            record = {key: "recorded basis" for key in ("title", "country", "region", "timeline", "change",
                                                        "mechanism", "impact", "boundary")}
            record.update(id="nl-net-metering", status="verified", reviewed="2026-10-06", tags=["solar"], sources=[
                {"kind": "official", "title": "Policy", "url": "https://example.org/policy", "note": "Scope"}])
            # As in the live snapshot: a free-text review note, and an unverified lead with no sources yet.
            lead = {**record, "id": "benelux-image-leads", "status": "unverified", "reviewed": "尚待核实",
                    "sources": [], "evidence_note": "截图线索"}
            (root / "market-policy" / "records.json").write_text(json.dumps(
                {"schema_version": 1, "reviewed": "2026-10-06", "records": [record, lead]}), encoding="utf-8")
            self.assertEqual(read_policies(root), market_policy.market_context(root)["records"])

    def test_digest_links_point_at_the_host_research_page(self):
        self.assertEqual(cli.PAGE, product_research.PAGE)


if __name__ == "__main__":
    unittest.main()
