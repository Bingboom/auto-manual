"""Refresh source input hashes after reviewed, source-local edits."""
from pathlib import Path
import hashlib
import json


def main():
    package = Path(__file__).resolve().parent
    path = package / 'source_manifest.json'
    manifest = json.loads(path.read_text())
    # Derived outputs are inventoried independently: embedding their hashes in
    # their own IR source manifest would create a circular hash dependency.
    manifest['inputs'] = [
        {'path': p.relative_to(package).as_posix(), 'size': p.stat().st_size,
         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(package.rglob('*'))
        if p.is_file() and p != path
        and '__pycache__' not in p.relative_to(package).parts
        and not p.relative_to(package).as_posix().startswith(
            ('validation/', '__pycache__/'))
    ]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
