"""Real IR fixture for release-envelope tests; only policy enrollment is injected."""
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from tools.word.bundle_html import build_word_bundle_html


def install_prepared_admission_fixture(test, markdown_dir, *, model, language, region="EU"):
    markup = (
        '<h1>Fixture</h1><h2 class="hb-spec-section"><span class="hb-spec-bullet">•</span><span class="hb-spec-section-text">INPUT</span></h2>'
        '<table class="manual-spec-table"><tbody><tr><td>Voltage</td>'
        '<td>100 V</td></tr></tbody></table>'
    )
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        page = root / "fixture.rst"
        page.write_text(".. raw:: html\n\n   " + markup + "\n", encoding="utf-8")
        bundle = SimpleNamespace(
            bundle_dir=root, page_dir=root, page_paths=(page,), title="Fixture",
            reference_doc=None, model=model, region=region, lang=language, languages=(language,),
        )
        output = root / "package"
        build_word_bundle_html({}, model, region, materialized_bundle=bundle,
                               output_dir=output, presentation_profile="web")
        shutil.copy2(output / "manual.ir.json", markdown_dir / "manual.ir.json")
    policy = {
        "target": {"model": model, "region": region, "language": language},
        "capabilities": {}, "expected_pages": ["fixture.rst"], "legacy_debt": [],
        "chapters": [{"id": "spec", "pages": ["fixture.rst"], "requirements": [
            {"id": "spec", "components": ["HB-TABLE-SPEC/vertical"], "minimum": 1},
        ]}],
    }
    patcher = patch("tools.web.component_admission.resolve_prepared_component_policy", return_value=policy)
    patcher.start()
    test.addCleanup(patcher.stop)
    return policy
