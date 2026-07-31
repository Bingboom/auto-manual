# Family-manifest diff carrier

The page manifests under `docs/manifests/` are currently the compatibility
source of truth. The family-manifest migration therefore starts with a
non-mutating carrier instead of rewriting all 17 files at once.

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
