# Family-manifest diff carrier

The page manifests under `docs/manifests/` are currently the compatibility
source of truth. The family-manifest migration therefore starts with a
non-mutating carrier instead of rewriting the full manifest inventory at once.

`tools/manifest_family.py` defines `family-manifest-diff/v1`:

```json
{
  "schema_version": "family-manifest-diff/v1",
  "base_manifest_id": "manual_us_single_en",
  "target_manifest_id": "manual_us_single_fr",
  "operations": [
    {"op": "replace", "path": "/manifest_id", "value": "manual_us_single_fr"}
  ]
}
```

Operations use JSON-Pointer paths and are ordered deterministically. Lists
with the same length are diffed item-by-item because page order is part of the
composition contract; a page-count change is represented as one explicit list
replacement so it cannot be mistaken for a harmless text edit.

The `roundtrip` command applies a carrier only to an in-memory copy of the base
manifest. It compares canonical UTF-8 bytes (sorted JSON keys, stable
indentation) so YAML whitespace and comments do not obscure semantic drift:

```bash
python tools/manifest_family.py roundtrip \
  --base docs/manifests/manual_us-single-en.yaml \
  --target docs/manifests/manual_us-single-fr.yaml \
  --diff /tmp/us-en-to-fr.family-diff.json
```

The first pilot covers the US English→French and US English→Spanish single
language lines. This PR does not rewrite source manifests, change build
assembly, or permit an external write. The subsequent manifest-folding PR
will add generated checked-in carriers only after the pilot remains byte
identical.

## Fold index

The tracked [`docs/manifests/family/index.yaml`](../../docs/manifests/family/index.yaml)
records four compatibility anchors and 16 target/diff pairs, covering all 20
current manifests. `BP@INTL` and `BP@JP` intentionally use separate anchors.
Run:

```bash
python tools/manifest_family.py fold \
  --root . \
  --index docs/manifests/family/index.yaml
```

The command checks that every `configs/config*.yaml`-backed manifest remains
covered, applies each carrier in memory, and compares canonical bytes with the
existing YAML golden. `--write` is an explicit carrier refresh operation; it
does not edit YAML or invoke an external source-table write.
