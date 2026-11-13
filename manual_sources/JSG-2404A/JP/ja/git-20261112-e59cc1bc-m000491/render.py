"""Hash-checked JSG Japanese source candidate through existing Manual IR replay.

Run with --output pointing to a new directory outside this source package.
No online table, publication, or release acceptance is written.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
ROOT = next(p for p in SOURCE.parents if (p / 'build.py').is_file())
sys.path.insert(0, str(ROOT))

from tools.manual_ir import read_manual_ir, write_manual_ir  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.prepared_style_audit import require_prepared_document_styles  # noqa: E402
from tools.web.symbol_asset_admission import require_symbol_asset_admission  # noqa: E402


def render(output: Path):
    reference = json.loads((SOURCE / 'source/reference.json').read_text())['rebuild']
    path = ROOT / reference['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != reference['sha256']:
        raise ValueError('pinned shared replay adapter changed')
    loader = importlib.util.spec_from_file_location('frozen_jp_replay', path)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    # This existing adapter is model-neutral: it reads the current candidate's
    # content and current hash inventory, never the reference's historical pins.
    module.SOURCE_ROOT = SOURCE
    module.rebuild(output)
    manifest = json.loads((SOURCE / 'source_manifest.json').read_text())
    path = output / 'manual.ir.json'
    ir = read_manual_ir(path)
    ir = replace(ir, metadata={**ir.metadata, 'frozen_source_manifest': manifest,
                              'publication_eligible': False,
                              'operator_source_acceptance': None,
                              'pending_source_review': manifest['pending_source_review']})
    require_prepared_document_styles(ir.to_dict(), stylesheet=(SOURCE / 'source/presentation.css').read_text(),
                                     exceptions=manifest['shared_component_exceptions'])
    write_manual_ir(ir, path)
    replay_package(output)
    symbols = require_symbol_asset_admission(output, SOURCE, manifest, ir.language)
    report = {'symbol_asset_admission_rows': len(symbols), 'model': ir.model, 'language': ir.language, 'chapters': len(ir.pages),
              'shared_style_admission': 'passed', 'publication_eligible': False,
              'original_source_sha256': manifest['original_source']['sha256']}
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    render(parser.parse_args().output.resolve())
