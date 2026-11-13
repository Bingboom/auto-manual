"""Re-inventory only this candidate; never changes the historical reference."""
from pathlib import Path
import hashlib
import json

SOURCE = Path(__file__).resolve().parent
ROOT = next(p for p in SOURCE.parents if (p / 'build.py').is_file())

def item(path, base):
    return {'path': path.relative_to(base).as_posix(), 'size': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def refresh():
    path = SOURCE / 'source_manifest.json'
    manifest = json.loads(path.read_text())
    content = json.loads((SOURCE / 'source/ja/content.json').read_text())
    manifest['chapter_source_pages'] = {c['id']: c['pages'] for c in content['chapters']}
    inputs = [p for p in SOURCE.rglob('*') if p.is_file()
              and p.name not in ['source_manifest.json', 'frozen_source_manifest.json']
              and not {'web', 'evidence', '__pycache__'} & set(p.relative_to(SOURCE).parts)]
    manifest['inputs'] = [item(p, SOURCE) for p in sorted(inputs)]
    deps = {ROOT / 'tools/markdown_bundle.py', ROOT / 'tools/build_paths.py'}
    for rel in ['tools/manual_ir', 'tools/component_specs', 'tools/web', 'tools/asset_pipeline',
                'tools/utils', 'docs/renderers/contracts']:
        deps.update(p for p in (ROOT / rel).rglob('*') if p.is_file()
                    and p.suffix in ['.py', '.css', '.json', '.yaml', '.yml'])
    ref = json.loads((SOURCE / 'source/reference.json').read_text())
    deps.update(ROOT / row['path'] for row in ref.values())
    deps.add(ROOT / 'docs/renderers/web/assets/shared/symbols/manifest.json')
    manifest['repo_inputs'] = [item(p, ROOT) for p in sorted(deps)]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(manifest['target']['model'], 'inputs', len(inputs), 'repo_inputs', len(deps))


if __name__ == '__main__':
    refresh()
