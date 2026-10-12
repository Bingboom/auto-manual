# Workflow guide: version tracking and diff export

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 9. Version Tracking and Diff Export

Because [`docs/_review/**`](../../docs/_review) is now the preferred review surface, you can keep cleaner RST history per target.

Recommended everyday workflow:

1. Pick the target you want to track.
2. Seed the review bundle once for that target.
3. Commit the review bundle as a Git baseline.
4. Edit the review bundle for normal review rounds.
5. If parameters changed in CSV, run `sync-review`.
6. Rebuild preview outputs from that review bundle and commit again.
7. Run `publish` for the formal release output, or run `diff-report` separately when needed.

### 9.1 First-Time Baseline

Use this when a target has never been tracked in Git before.

Example baseline:

```powershell
python build.py review --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Add JE-1000F US review baseline"
```

What this means:

- `review` prepares [`docs/_build/<model>/<region>/rst/**`](../../docs/_build) from template/data
- then it seeds [`docs/_review/<model>/<region>/**`](../../docs/_review)
- the commit becomes the starting point for future report comparisons

### 9.2 Daily Update Flow

After the baseline exists, the normal update loop is:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py word --config configs/config.us-en.yaml --model JE-1000F --region US
git add docs/_review/JE-1000F/US
git commit -m "Update JE-1000F US manual"
```

Recommended rule:

- `_review` is now the normal authoring source after review starts
- if a round also changed shared template/data, commit those with `_review`
- use `review --refresh-review` only when intentionally reseeding from the shared seed layer
- use `sync-review` after parameter changes in [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv) so review keeps up with regenerated values

### 9.3 Which `tracked-root` to Use

Use the tracked root that matches the scope you want to compare:

- one model across all tracked regions:
  [`docs/_review/JE-1000F`](../../docs/_review/JE-1000F)
- one model and one region:
  [`docs/_review/JE-1000F/US`](../../docs/_review/JE-1000F/US)
- temporary runtime-only comparison:
  [`docs/_build/JE-1000F`](../../docs/_build/JE-1000F)

Recommended default:

- prefer `_review`
- use `_build` only for temporary debugging when you have not emitted a review bundle yet

Example report export for one model:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F --from-ref HEAD~1 --to-ref HEAD --include-initial-adds
```

Example report export for one region:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref HEAD~3 --to-ref HEAD
```

### 9.4 How to Compare Two Specific Commits

If you want to compare a baseline commit with the latest manual state:

```powershell
python build.py diff-report --config configs/config.us-en.yaml --tracked-root docs/_review/JE-1000F/US --from-ref <old_commit> --to-ref <new_commit>
```

Examples:

- compare the previous commit to the current one:
  `--from-ref HEAD~1 --to-ref HEAD`
- compare the baseline commit to current head:
  `--from-ref a1b2c3d --to-ref HEAD`
- compare two tags or branches:
  `--from-ref release/v1 --to-ref release/v2`

Default outputs:

- [`reports/version_tracking/JE-1000F/US/*_files.csv`](../../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_files.html`](../../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.csv`](../../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_pages.html`](../../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.csv`](../../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_fields.html`](../../reports/version_tracking/JE-1000F/US)
- [`reports/version_tracking/JE-1000F/US/*_index.html`](../../reports/version_tracking/JE-1000F/US)
- legacy report path aliases remain available as [`reports/version_tracking/JE-1000F/US/*.csv`](../../reports/version_tracking/JE-1000F/US) and `*.html`

Use `--report-dir` if you want a different output folder.

Useful option:

- `--include-initial-adds`
  The default report already hides one-time initial baseline Added rows. Use this only when you want to see the full first-import churn.

Automatic behavior:

- if the tracked subtree does not exist at `from-ref` but exists at `to-ref`, the report now shows an explicit note that this is an initial baseline and all Added rows are expected
- by default, the generated reports keep the note but suppress those initial Added rows
- if you pass `--include-initial-adds`, those initial Added rows are kept in the generated reports

### 9.5 Which Report to Open First

Open order:

1. `*_index.html`
2. `*_fields.html`
3. `*_pages.html`
4. `*_files.html`

Why:

- `index` gives the report homepage and target jump links
- `fields` is usually the most useful review view because it shows rendered value changes and source back-mapping
- `pages` is the next best rollup when you want page-level impact
- `files` is best when you need raw file churn, insertions, and deletions

What each report means:

- `files`: which tracked `.rst` files changed, plus insertions and deletions
- `pages`: page-level rollup with `fields_changed` counts
- `fields`: structured field/value changes extracted from list-tables and `Label: Value` lines
  For generated `spec_*.rst` pages, the report now also tries to fill `source_row_key`, `source_section_key`, `source_line_order`, and `source_csv_line` from [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv).
  For template-based pages such as `03_product_overview`, `05_operation_guide`, and `12_app_setup`, the report also tries to back-map changed field text to matching page-value rows by comparing rendered values against resolved placeholders.
  `fields.html` now includes built-in filters for `model`, `region`, `page_key`, `source_row_key`, `change_type`, plus a full-text search box.
- `index`: homepage that links `files/pages/fields` together and provides target-level jump links with filters pre-applied

### 9.6 How to Read `fields` Back-Mapping

Important columns in `*_fields.csv` and `*_fields.html`:

- `field_key`: the rendered field label found in the RST content
- `old_value` / `new_value`: the rendered before/after values
- `source_row_key`: the matched source row in [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv)
- `source_section_key`: the matched source section in [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv)
- `source_line_order`: the matched source line order for multiline rows
- `source_csv_line`: the original CSV line number
- when a field label itself changes, the diff now first tries to pair old/new rows through stable source back-mapping before falling back to rendered label text, so placeholder/spec renames are more likely to show up as one `M` row with both `old_value` and `new_value`

Interpretation rule:

- if `source_row_key` is filled, the report found a source row match
- if it is blank, the row is still useful as a rendered text diff, but the source mapping was not reliable enough to fill automatically

### 9.7 Typical Review Example

For a normal JE-1000F US review cycle:

```powershell
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py check --config configs/config.eu-en.yaml --model JE-1000F --region EU
git add docs/_review/JE-1000F/US
git commit -m "Refresh JE-1000F US manual"
python build.py publish --config configs/config.us-en.yaml --model JE-1000F --region US
```

Then:

1. open [`reports/version_tracking/JE-1000F/US/*_index.html`](../../reports/version_tracking/JE-1000F/US)
2. click the `JE-1000F/US` target link
3. open `fields`
4. filter `source_row_key` when you want to inspect one spec or placeholder family

### 9.8 Common Mistakes

- Comparing `_build` after a fresh clean without rebuilding the same target first
- Running `review --refresh-review` without realizing it will replace the current review bundle
- Changing parameter CSV data during review and forgetting to run `sync-review`
- Forgetting that `check/html/word/pdf` now use review content by default once review exists
- Committing only `_review` when the round also changed shared template or CSV logic
- Reading `files.html` first and missing the more useful field-level diff in `fields.html`
