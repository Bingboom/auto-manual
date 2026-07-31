# JP Production IDML Smoke Acceptance — 2026-07-31

## Scope

This record covers Workstream W Stage 5 item 12: export the JE-1000F/JP
single-language family through the real `build.py idml` production path, then
run the repository's structural `check_idml` validation. The source snapshot is
the committed `tests/fixtures/phase2` fixture, so the run is credential-free
and repeatable without reading mutable Feishu data.

The run started from `origin/main` commit `cf627076` (PR #835). Generated PDF,
RST, Manual IR, page-plan, and IDML files stayed under `docs/_build` in an
isolated worktree and were not committed.

## Rejected baseline

The first command completed and `check_idml` returned OK, but the generated
`manual.ir.json` reported top-level `language: en` while its frozen manifest
declared `languages: [ja]`. The high-level IDML dispatch forwarded model,
region, data root, and mode, but not the sole language from `config.ja.yaml`;
the low-level exporter therefore used its historical English default.

That result was rejected. It proves why structural package validation alone is
not a locale-routing acceptance gate.

## Corrected run

`build.py idml` now forwards the sole `build.languages` value for a
single-language config when no explicit `--lang` is present. Explicit `--lang`
still wins, and a multilingual config continues to use its existing default.

Commands:

```bash
python build.py idml \
  --config configs/config.ja.yaml \
  --model JE-1000F \
  --region JP \
  --source runtime \
  --data-root tests/fixtures/phase2 \
  --idml-mode production

python tools/export_idml.py \
  --check docs/_build/JE-1000F/JP/idml/manual_je1000f_jp.idml
```

Observed exporter command includes `--lang ja`. Acceptance evidence:

| Check | Result |
| --- | --- |
| `check_idml` | OK, zero structural issues |
| Manual IR language | `ja` |
| Frozen declared languages | `ja` |
| Manual IR pages / blocks | 13 / 262 |
| Manual content SHA-256 | `34c3f1b60af835996fc4d66c45bc0806dbcaeae1153620f0fc57d550fb8f7711` |
| Layout-params SHA-256 | `810c12153a167169da545ba5f19e03d618618058db6abca06b192353a704e188` |
| IDML ZIP parts | 128 |
| Stories / spreads | 93 / 28 |
| Story parts with explicit Arial Unicode MS CJK runs | 45 |
| LaTeX measured physical pages | 22 |
| Fallback source-page match | 11/13 (84.6%) |

The raw IDML ZIP SHA-256 is deliberately not an acceptance identity: package
timestamps and the fallback measured-reference artifact can vary between
otherwise equivalent local runs. The stable content and layout identities
come from the Manual IR; byte-level renderer regression remains covered by the
committed Japanese golden package.

## Result and boundary

Acceptance: **passed** for JP language routing and structural production-IDML
export.

This does not approve fixture prose, the fallback page match, a production
reference-layout plan, link portability, native InDesign composition, overset
preflight, or PDF parity. Those remain separate package/finalize/parity gates;
`check_idml` only proves package structure.
