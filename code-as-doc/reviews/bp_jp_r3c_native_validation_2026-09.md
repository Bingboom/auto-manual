# JBP-2000B JP R3c native IDML validation (2026-09)

**Status: shell. The pipeline half is filled in and reproducible; the native
half is empty because it can only be produced on the design Mac.**

This is the document `code-as-doc/reviews/` was missing. Its EU and US
counterparts exist — `jbp2000b_eu_r2_native_validation_2026-08.md` and
`jbp2000b_us_s6_reconciliation_2026-08.md` — and JP had only the pipeline-side
`bp_jp_reference_vs_built_2026-09.md`. R3c Phase 6 records that a native round
happened on 2026-09-01 and that the styling did not yet meet acceptance, but
adds "the specific findings are on the operator's host and are not reproduced
here", so nothing in the repo says what was seen or which items are now closed.
That gap is what this file exists to close: fill the empty cells on the host
rather than transcribing findings into a chat message.

## Decision and scope

The frozen artefact is the JP battery-pack booklet as built from this branch.
Freezing it means freezing everything in the table below, including the two rows
of residual debt that `bp_jp_reference_vs_built_2026-09.md` §7 records as *not*
measurements.

Out of scope for this round, by the operator's closeout ruling: public IR, Web,
and data-reading rules are subsequent system work and are not to be added to
this line.

## Build evidence (filled — reproducible off-host)

```bash
python3 build.py idml --config configs/config.bp-jp.yaml --model JBP-2000B --region JP
```

| Pipeline gate | Result |
| --- | --- |
| Package | `docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml` |
| Zip members | `107` |
| Spreads | `12` |
| Stories | `88` |
| Prose pages | `10` |
| Spec rows / LCD rows / troubleshooting rows | `11 / 2 / 13` |
| Skipped raw blocks | `0` |
| Content digest (member-name + member-content sha256, order-independent of zip metadata) | `a7cc780f2fb6a6ce299cec6cb7027df8b08ec8c2810b0473165a0b5eefd7ebf1` |

The digest is the freeze pin. It hashes each member's name and its content, so
it is stable across rebuilds (zip timestamps are excluded) and changes if any
byte of any member changes. Recompute it with the snippet in "Method" below and
compare, rather than trusting a rebuild to "look the same".

## Native InDesign evidence (empty — needs the design Mac)

Run on a host whose InDesign matches the committed pin
`tools/idml/indesign_version_pin.json` → `Adobe InDesign 2026 21.0.1.6`.
`--check-host` refuses a mismatch; `--allow-version-mismatch` records the
override into the report's toolchain block rather than hiding it.

```bash
python3 tools/indesign_finalize.py \
  --idml docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml \
  --indd docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp_r1.indd \
  --pdf  docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp_r1.pdf \
  --report docs/_build/JBP-2000B/JP/idml/finalize_report_r1.json
```

The `--report` path is deliberately inside `docs/_build/JBP-2000B/JP/`, which is
what §4 of the reference-versus-built ledger asked for: the findings stay
readable in the tree instead of being transcribed.

| Native gate | Result |
| --- | --- |
| InDesign version (must match the pin) | |
| Pages | |
| Overset stories / nested table cells | |
| Missing fonts / glyphs / bad links | |
| PDF glyph validation | |
| PDF standard | |
| Output intent / condition | |
| INDD SHA-256 | |
| PDF SHA-256 | |
| Finalize-report SHA-256 | |

Overset is the one gate that cannot be pre-answered: `_overset_pages` in
`tools/indesign_finalize.py` reads a report the JSX writes inside the
application. Phase 6's earlier zeros were retired by #996 because they described
bytes that no longer exist — do not carry them forward.

## Phase 6 acceptance criteria

| # | Criterion | Result | Evidence |
| ---: | --- | --- | --- |
| 1 | Native import, save, reopen and PDF/X-4 export complete with overset 0, missing fonts 0, missing glyphs 0, bad links 0 | | |
| 2 | The twelve pages match the approved master as a **structural key** — which heading takes which style, which table takes which component. Geometry is explicitly *not* the test: the operator's 2026-09-03 ruling is that the hand-made PDF carries production error and styles are shared across regions | | |
| 3 | Japanese weight renders as intended across the hierarchy | | |

## Twelve-page visual ledger

Fill "Result" with pass, or with what is wrong. The "Watch for" column is
pre-seeded from the pipeline-side findings so the round is not starting cold.

| Page | Role | Watch for | Result |
| ---: | --- | --- | --- |
| 01 | cover | Placed approved asset, not live text — confirm it is the JP cover and not a substituted one | |
| 02 | toc | Dot leaders are a leader tab, not literal `.` characters; all ten entries and the `01-10` range marker present. **§6 open item: the page 02/03 heading structure** | |
| 03 | safety | Bullet marker: the build sets `•` U+2022 where the master sets `・` U+30FB (§4d, unactioned). **§6 open item: the master's page 2 has no bullet list at all** | |
| 04 | symbols | Signal labels, rows and rounded shells fit | |
| 05 | inbox | Card, content and tip panels use the JP-only heights (`lang_jp_idml_inbox_compact_*`, card 145.0 / content 119.0) | |
| 06 | product_overview | Figure callouts inside the illustrations | |
| 07 | lcd | LCD icon table composition | |
| 08 | operation_guide | | |
| 09 | connections | The `stacking_guide` variant is JP-declared; its three rows sit in the compact overlay | |
| 10 | charging | Figure measure, suffix pill, redacted labels (§4a) | |
| 11 | troubleshooting | Label-column tint; the shell is a fixed-height anchored group while the table flows across two spreads | |
| 12 | spec + warranty | **The one question this round must answer**: `HB Warranty Body` is `PointSize 6` with `<Leading type="unit">6</Leading>` — it sets **solid**. Its siblings `HB Warranty Note` and `HB Warranty Lead` carry 7.2 and 8.2 against sizes 6 and 7. Does the master's warranty prose set solid, or does it breathe? See §4 of the ledger for why the old "is the `Leading="7"` override dropped" question is void | |

## Residual debt this freeze locks in

Both rows are live in the frozen book and neither came off the master. Full
reasoning in `bp_jp_reference_vs_built_2026-09.md` §7.

| Row | Value | Why it is not a measurement |
| --- | --- | --- |
| `lang_jp_idml_warranty_lead_height` | `40` | CANDIDATE-STAGE (#1019). Natural three-line height is 34.60 pt, so it carries +5.40 pt with no content reason |
| `lang_jp_idml_warranty_panel_height_adjust_7` | `5.5` | JP-only compensation for a **shared** budget/render mismatch (`_section_body` budgets 6.0, `bp_default` renders 7.0); retired by the shared fix, which is deferred because it grows every US and EU panel |

## Artifacts to attach

1. `manual_jbp2000b_jp_r1.indd`
2. `manual_jbp2000b_jp_r1.pdf` (PDF/X-4)
3. `finalize_report_r1.json` — inside `docs/_build/JBP-2000B/JP/`
4. Page renders at 180 dpi for any page whose Result is not "pass"

`docs/_build/**` is generated and excluded from commits; reference the artifacts
by path and digest here rather than committing them.

## Method

Recompute the freeze digest:

```python
import hashlib, zipfile
z = zipfile.ZipFile("docs/_build/JBP-2000B/JP/idml/manual_jbp2000b_jp.idml")
h = hashlib.sha256()
for name in sorted(z.namelist()):
    h.update(name.encode())
    h.update(hashlib.sha256(z.read(name)).digest())
print(h.hexdigest())
```

A mismatch means the build moved; diff member-by-member before assuming the
freeze is stale, because a changed member names the change.
