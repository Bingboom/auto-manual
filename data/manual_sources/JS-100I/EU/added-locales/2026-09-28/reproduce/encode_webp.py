"""Encode native JS-100I PNG derivatives losslessly for the Web release."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, features


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(root: Path) -> list[dict]:
    assets = root / 'docs/renderers/web/assets'
    inputs = sorted((assets / 'js100i_eu_shared').glob('*.png'))
    inputs += sorted((assets / 'js100i_eu_added').glob('views_*.png'))
    if len(inputs) != 24:
        raise ValueError('Expected exactly 24 native PNG derivatives')
    rows = []
    for source in inputs:
        target = source.with_suffix('.webp')
        with Image.open(source) as original:
            original.save(target, 'WEBP', lossless=True, quality=100, method=6, exact=True)
            rgba = original.convert('RGBA').tobytes()
            with Image.open(target) as encoded:
                if encoded.size != original.size or encoded.convert('RGBA').tobytes() != rgba:
                    raise ValueError(f'Lossless encoding changed pixels: {source}')
            rows.append({'source': source.relative_to(root).as_posix(), 'source_sha256': sha(source),
                         'output': target.relative_to(root).as_posix(), 'output_sha256': sha(target),
                         'rgba_sha256': hashlib.sha256(rgba).hexdigest(),
                         'width': original.width, 'height': original.height,
                         'source_bytes': source.stat().st_size, 'output_bytes': target.stat().st_size})
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    receipt = {'format': 'WebP lossless', 'libwebp': features.version('webp'),
               'settings': {'lossless': True, 'quality': 100, 'method': 6, 'exact': True},
               'files': encode(args.repo_root.resolve())}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
