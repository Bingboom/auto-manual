# Manual intake assistance

Status: active

Review preparation tooling. It does not assemble or publish a manual,
confirm an English baseline, or validate translation semantics.

## One bounded task per operator handoff

An English intake uses an existing English sibling IR as a structural candidate.
Supply the new model's original source and physical pages. A locale intake uses
the final English IR and that locale's original pages. Neither case may inherit
technical copy merely because its structure is similar. Complete one language
and hand it off before waiting for the remaining languages.

```bash
python -m tools.manual_intake_assist packet \
  --reference-ir /path/to/english/manual.ir.json \
  --source /path/to/original.ai --model MODEL --region EU --language fr \
  --pages 2 15 16 17 18 19 20 21 22 79 \
  --output /path/to/new-work/packet.json
```

Replace the sample pages with the actual source's physical page map. Frontmatter
and shared legal pages are explicit inputs. PDF-compatible AI is supported;
outlined text still requires visual reading. The tool records source hashes,
original text blocks, copy occurrences, component identities and image hashes.
Structured list items are included even when a component, such as FCC, has no
duplicate HTML carrier; removing a required bullet fails the completeness check.
It never extracts or crops an image. Reference IR, source and target must be
supplied again for checking, so deleting candidate rows does not reduce the
expected work.

Only fill each item's `native`, `physical_page`, `evidence`, `decision`:

- `native-copy`: native original wording, with source page/block or visual
  transcription evidence; keep values, units, warnings and legal content.
- `source-identical`: exact original text is intentionally unchanged, with
  evidence (for example an original-language legal line or model marking).
- Leave unresolved work `pending`. Do not insert English fallback, invented
  translations or speculative values to clear the report.

Natural wrapping and longer wording are accepted. Component/table differences,
new paragraphs or image variants go through existing manifest family/diff and
baseline exception review; never alter the locked occurrences or use this copy
map to conceal missing source content. Repeated identical copy within a chapter
is grouped, with every occurrence exposed. If occurrences require different
wording, resolve the structural mapping first rather than apply a global replace.

```bash
python -m tools.manual_intake_assist check-copy \
  --reference-ir /path/to/english/manual.ir.json \
  --source /path/to/original.ai --model MODEL --region EU --language fr \
  --pages 2 15 16 17 18 19 20 21 22 79 \
  --packet /path/to/new-work/packet.json \
  --output /path/to/new-work/check-1.json \
  --copy-map /path/to/new-work/native-copy.json
```

Exit 1 means unresolved/missing/changed items; errors identify the item or locked
binding and next action. The optional copy-map is created only when the checklist
is complete, in the existing `copy_by_page` + evidence format. This is a reviewed
input handoff, not a new renderer or automatic IR translation. Use existing
prepared/native assembly, component admission, fresh sealing and Web publication.
A complete map is not proof that the original's every paragraph was captured;
source coverage and desktop/390px mobile inspection remain independent acceptance.
All outputs refuse replacement of an existing file or report directory.

## Shared artwork comes first

Ownership stays in the existing tables:

| Kind | Primary source |
| --- | --- |
| LCD status icons | LCD icons `figure` attachment and native descriptions |
| Safety/compliance symbols | Symbols `Figure` attachment and native copy |
| Solar panels, car charging, cables, general illustrations | Asset definitions and exports, with source records |

Do not create another icon collection. Do not treat an `ALL` scope or duplicate
bytes as proof of universal suitability. Check connector type, product drawing,
wiring, panel count, region marks, embedded text and the target's approved visual
binding. LCD/car/solar status icons remain in LCD icons, not the illustration set.

`art-review` consumes full paginated read-only live snapshots named
`live-{definitions,exports,lcd,symbols}.json`, each a list of
`{record_id, fields}`. Dedicated-table attachment downloads may add
`download_sha256` (computed from the downloaded original) and live under
`snapshots/downloads`. Feishu reading/writing follows the
[existing Bitable skill](../../.agents/skills/lark-cli-bitable-ops/SKILL.md).

```bash
python -m tools.manual_intake_assist art-review \
  --repo /path/to/auto-manual --snapshots /path/to/live-snapshot \
  --output /path/to/new-shared-art-review
```

The inventory covers tracked images in `docs` and `manual_sources`, plus dedicated
attachment downloads. It groups only identical SHA256 bytes, preserves all source
paths and original registry scopes, and separates actual downloaded attachment
matches from export-table hash declarations. Missing files and registry entries
without a matching scanned raster/SVG are visible. PDF-only/vector source entries
are not proof of missing artwork; review them separately.

The portable HTML gallery lets the operator filter, inspect and export selections.
Selection export is review input, not an approved registry update. Persist the
selection before refreshing. Confirm exact rows/scopes before the archive step;
then write existing rows additively, upload original bytes, read back every record
and download/hash-check the attachments. No live writes are performed by this tool.

## Operator selections and readable artwork identities

Import the exported review JSON with `art-review --selections /path/to/shared-art-selections.json`.
Conditional reuse notes remain conditional; an exclusion removes that byte version from the
priority view. Operation/button artwork is excluded from shared-art priority and cannot receive
a reuse selection. This excludes artwork only, not shared rendering components.

`--identities /path/to/identity-review.json` accepts `items` containing `id`, full `sha256`,
`label`, `canonical_id` and `evidence`. The agent first compares matching artwork, preserves
source/target distinctions and proposes an existing canonical original. Unknown/duplicate IDs,
a changed hash, a missing label/evidence or a cross-category canonical reference fail.
Annotations change review labels and record proposed aliases; they do not replace source files,
approve new scope, merge registry rows or write Feishu. Perceptual similarity is a screening aid,
not proof of equivalent wiring or symbols.

Solar art keeps its existing SolarSaga model/count caption as the human-readable identity.
Car/car-cable explanatory text belongs to native HTML and caption frames to shared CSS.
Small LCD and safety symbols require real transparency. Match source-visible symbol semantics
before reuse; retain count/style variants when their meaning differs. See the
[Web artwork contract](../../docs/renderers/contracts/STYLE_DEFINITION.md#新录入网页的图文分工).

## Sol handoff and acceptance boundary

Give the executor the source/page map, English reference and one generated packet,
plus confirmed shared-art selections. It should fill the explicit copy fields,
run `check-copy`, and report unresolved IDs. It must not write a temporary renderer,
recrop already selected art or approve its own English baseline. New layout or
source ambiguity is returned as a specific chapter/slot difference.

Current automation covers work-item enumeration and mechanical completeness only.
A GPT-6.1 Sol trial must use the actual requested model on one complete English
chapter and one corresponding native chapter, then receive independent semantic,
asset and desktop/mobile acceptance. Deterministic tests or another model's run
cannot be reported as that model's acceptance.

For visual normalization, inspect SVG originals in the browser: some raster
preview converters misrender clip paths or transforms. A broken contact-sheet
preview alone is not evidence of a broken original. Record reference-only
fragments and excluded defects separately from proposed reusable originals.
