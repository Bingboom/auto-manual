# Phase2 Lark Setup And Parity Plan

Updated: 2026-04-04

Archived note:

- this file is a one-time machine bring-up and parity record
- use [`build_doc_guide.md`](build_doc_guide.md) and [`../user-guide/hello_auto-doc.md`](../user-guide/hello_auto-doc.md) for the current maintained workflow

This file is a short execution plan for the next machine.
It covers:

- enabling local `lark-cli`
- wiring the `FEISHU_PHASE2_*` environment variables
- running one disposable `phase1` vs `phase2` parity check without polluting the main workspace

Reference:

- official CLI README: [larksuite/cli](https://github.com/larksuite/cli)
- current repo implementation: [`build.py`](../build.py), [`tools/sync_data.py`](../tools/sync_data.py), [`tools/data_snapshot.py`](../tools/data_snapshot.py)

## 1. Goal

Exit criteria:

1. `python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` succeeds on the new machine.
2. `python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2` succeeds and refreshes [`data/phase2/snapshot_manifest.json`](../data/phase2/snapshot_manifest.json).
3. One explicit target parity run proves that `phase1` and `phase2` produce identical or expected-difference outputs.
4. The parity run keeps generated `docs/_build/`, `reports/version_tracking/`, and `reports/releases/` under an isolated staging root instead of polluting the main working copy.

## 2. Part A: Enable `lark-cli`

The official README currently documents this install and login flow:

```bash
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
lark-cli config init --new
lark-cli auth login --recommend
lark-cli auth status
```

Execution steps:

1. Install Node.js and confirm `npm` is available.
2. Install the CLI:
   - `npm install -g @larksuite/cli`
   - `npx skills add larksuite/cli -y -g`
3. Run one-time app setup:
   - `lark-cli config init --new`
4. Complete interactive login:
   - `lark-cli auth login --recommend`
5. Verify login:
   - `lark-cli auth status`

Stop condition:

- do not continue until `lark-cli auth status` shows a valid authenticated session

## 3. Part B: Wire `FEISHU_PHASE2_*`

The current shared config expects these environment variables:

- `FEISHU_PHASE2_BASE_TOKEN`
- `FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID`
- `FEISHU_PHASE2_SPEC_ROWS_SOURCE_VIEW_ID`
- `FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID`
- `FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_VIEW_ID`
- `FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID`
- `FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID`
- `FEISHU_PHASE2_SPEC_NOTES_TABLE_ID`
- `FEISHU_PHASE2_SPEC_NOTES_VIEW_ID`
- `FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID`
- `FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID`
- `FEISHU_PHASE2_LCD_ICONS_TABLE_ID`
- `FEISHU_PHASE2_LCD_ICONS_VIEW_ID`
- `FEISHU_PHASE2_TROUBLESHOOTING_TABLE_ID`
- `FEISHU_PHASE2_TROUBLESHOOTING_VIEW_ID`
- `FEISHU_PHASE2_VARIABLE_DEFAULTS_TABLE_ID`
- `FEISHU_PHASE2_VARIABLE_DEFAULTS_VIEW_ID`
- `FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_TABLE_ID`
- `FEISHU_PHASE2_VARIABLE_LANG_OVERRIDES_VIEW_ID`
- `FEISHU_PHASE2_MANUAL_COPY_SOURCE_TABLE_ID`
- `FEISHU_PHASE2_MANUAL_COPY_SOURCE_VIEW_ID`
- `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`
- `FEISHU_TRANSLATION_MEMORY_TABLE_ID`
- `FEISHU_TRANSLATION_MEMORY_VIEW_ID`

Optional maintenance-only bindings for `spec-master-rebuild --bootstrap-source-tables`:

- `FEISHU_PHASE2_DOCUMENT_KEY_TABLE_ID`
- `FEISHU_PHASE2_ROW_KEY_TABLE_ID`

Execution steps:

1. Collect the Base token plus every source table/view ID from Feishu. Mirror repositories should keep these values in environment variables or GitHub Secrets, not in committed config.
2. Export them in the shell profile used on the new machine.
3. Open a new shell and verify:

```bash
printenv | rg '^FEISHU_PHASE2_'
```

4. Run the repo-level smoke test:

```bash
python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run
```

5. If the dry-run passes, run the real sync:

```bash
python3 build.py sync-data --config configs/config.us.yaml --data-root data/phase2
```

6. Confirm these local generated outputs changed as expected. `data/phase2/` is gitignored, so this verification should not become a code commit unless a task explicitly asks for a checked-in fixture:
   - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
   - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
   - [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
   - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv), generated from Manual Copy Source plus tagged Translation Memory
   - [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
   - [`data/phase2/row_key_mapping.csv`](../data/phase2/row_key_mapping.csv)
   - [`data/phase2/snapshot_manifest.json`](../data/phase2/snapshot_manifest.json)

Failure triage:

- if `sync-data` fails before any API call, check missing `FEISHU_PHASE2_*`
- if `sync-data` fails on auth, rerun `lark-cli auth status`
- if `sync-data` fails on table access, re-check the specific table/view ID pair

## 4. Part C: Run Parity With An Isolated Staging Root

`build.py` now supports `--staging-root`, so parity no longer needs a disposable worktree just to keep generated outputs out of the tracked repo paths.
Use the main repo checkout, but redirect generated `docs/_build`, `reports/version_tracking`, and `reports/releases` into `.tmp/parity/...`.

Recommended target:

- config: [`configs/config.us.yaml`](../configs/config.us.yaml)
- model: `JE-1000F`
- region: `US`

Execution steps:

1. Create isolated staging folders:

```bash
mkdir -p .tmp/parity/phase1 .tmp/parity/phase2
```

2. Create a scratch folder for captured comparison artifacts:

```bash
mkdir -p .tmp/parity
```

3. Capture the `phase1` baseline:

```bash
python3 build.py rst --config configs/config.us.yaml --model JE-1000F --region US --source runtime --data-root data/phase1 --staging-root .tmp/parity/phase1
python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US --data-root data/phase1 --staging-root .tmp/parity/phase1
python3 build.py release-manifest --config configs/config.us.yaml --model JE-1000F --region US --data-root data/phase1 --staging-root .tmp/parity/phase1
```

4. Capture the `phase2` build:

```bash
python3 build.py rst --config configs/config.us.yaml --model JE-1000F --region US --source runtime --data-root data/phase2 --staging-root .tmp/parity/phase2
python3 build.py check --config configs/config.us.yaml --model JE-1000F --region US --data-root data/phase2 --staging-root .tmp/parity/phase2
python3 build.py release-manifest --config configs/config.us.yaml --model JE-1000F --region US --data-root data/phase2 --staging-root .tmp/parity/phase2
```

5. Compare the outputs:

```bash
diff -ru .tmp/parity/phase1/docs/_build/JE-1000F/US/rst .tmp/parity/phase2/docs/_build/JE-1000F/US/rst > .tmp/parity/rst.diff || true
```

Focus areas:

- `spec_*.rst`
- `symbols_*.rst`
- `product_name` resolution
- release-manifest payload

Expected result:

- rendered content should be identical if the phase2 snapshot is still a faithful copy of phase1
- allowed differences are path-level traceability fields that point to `data/phase1/...` vs `data/phase2/...`

If the RST diff is not empty:

1. identify whether the difference comes from content rows or only from snapshot source paths
2. if content differs, inspect the matching CSV row in both `data/phase1` and `data/phase2`
3. only consider switching defaults to phase2 after content parity is explained and accepted

## 5. Part D: Wrap Up

When the parity run is complete:

1. keep `.tmp/parity/rst.diff` and any copied manifests long enough to review
2. record the result in the next commit or PR note
3. remove the disposable worktree when no longer needed:

```bash
git worktree remove ../auto-manual-parity
```

## 6. 2026-04-01 Execution Result

Status on this machine:

1. Part A completed: local `Node.js`, `npm`, and `lark-cli` are installed, configured, and authenticated.
2. Part B completed: `FEISHU_PHASE2_*` is wired, `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2 --dry-run` succeeds, and the real sync refreshed [`../data/phase2/snapshot_manifest.json`](../data/phase2/snapshot_manifest.json).
3. Part C completed in the disposable worktree `C:/Users/tangxb/Documents/GitHub/auto-manual-parity`.

Captured parity artifacts for the real synced snapshot are kept under:

- `C:/Users/tangxb/Documents/GitHub/auto-manual-parity/.tmp/parity_real_sync_20260401T110943/`

Observed result for target `configs/config.us.yaml + JE-1000F + US`:

- `phase1` and `phase2` both passed `rst`
- `phase1` and `phase2` both passed `check`
- `release-manifest` raw differences are limited to `built_at` plus snapshot path fields pointing to `data/phase1/...` vs `data/phase2/...`
- normalized `release-manifest` payloads are equal after ignoring `built_at` and phase-root path strings

RST comparison summary:

- expected traceability difference: [`bundle_manifest.json`](../../auto-manual-parity/.tmp/parity_real_sync_20260401T110943/phase2_build/rst/bundle_manifest.json) points to `data/phase2/Spec_Master.csv` with the synced snapshot SHA instead of the retired historical `data/phase1/Spec_Master.csv`
- one real content delta remains in [`spec_en.rst`](../../auto-manual-parity/.tmp/parity_real_sync_20260401T110943/phase2_build/rst/generated/JE-1000F/spec_en.rst) and [`spec_en.rst`](../../auto-manual-parity/.tmp/parity_real_sync_20260401T110943/phase2_build/rst/page/spec_en.rst)
- concrete difference: `AC Output in Bypass Mode` with the footnote marker in phase1 became plain `AC Output in Bypass Mode` in phase2
- initial observed source difference: the retired historical `data/phase1/Spec_Master.csv` kept `Row_label_footnote_refs=ac_bypass` on the `JE-1000F_US_en + ac_output_bypass` row, while the first synced [`../data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv) copy left that field empty

Interpretation:

- the real phase2 snapshot is operational and build-valid on this machine
- release-manifest parity is effectively clean
- the first parity run still had one content delta, pending root-cause confirmation

Initial next action that was investigated:

1. restore `Row_label_footnote_refs=ac_bypass` for the `JE-1000F_US_en / ac_output_bypass` row in the Feishu source table
2. rerun `python build.py sync-data --config configs/config.us.yaml --data-root data/phase2`
3. rerun this disposable parity check and confirm the remaining `spec_en.rst` delta disappears

Follow-up on 2026-04-01:

- Feishu source data was already correct; the real cause was the sync implementation
- `lark-cli base +record-list` abbreviated long headers such as `Row_label_footnote_refs` to `Row_label_footnote_r...`
- the previous sync path matched returned columns by display name only, so that field was dropped during CSV normalization
- after fixing [`../tools/sync_data.py`](../tools/sync_data.py) to resolve full field names via `base +field-list`, rerunning `sync-data` restored `Row_label_footnote_refs=ac_bypass` in [`../data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- a second disposable parity run under `C:/Users/tangxb/Documents/GitHub/auto-manual-parity/.tmp/parity_real_sync_20260401T112147/` removed the remaining `spec_en.rst` delta
- current parity status is now clean except for the expected traceability-only `bundle_manifest.json` path/SHA difference and the expected `release-manifest built_at + phase path` differences

## 7. Decision Rule

This parity plan is historical. The default structured-data source has now moved to `phase2`.
Do not use the old phase1 parity baseline as an active build, review, or publish source.

The original switch criteria were:

1. `sync-data` is reproducible on the new machine
2. one target parity run is clean
3. any remaining release-manifest or diff-report path-only deltas are understood
