# Phase2 Lark Setup And Parity Plan

Updated: 2026-04-01

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

1. `python3 build.py sync-data --config config.yaml --data-root data/phase2 --dry-run` succeeds on the new machine.
2. `python3 build.py sync-data --config config.yaml --data-root data/phase2` succeeds and refreshes [`data/phase2/snapshot_manifest.json`](../data/phase2/snapshot_manifest.json).
3. One explicit target parity run proves that `phase1` and `phase2` produce identical or expected-difference outputs.
4. The parity run does not touch the main working copy's `docs/_build/`, `docs/_review/`, `reports/version_tracking/`, or `reports/releases/`.

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
- `FEISHU_PHASE2_SPEC_MASTER_TABLE_ID`
- `FEISHU_PHASE2_SPEC_MASTER_VIEW_ID`
- `FEISHU_PHASE2_SPEC_FOOTNOTES_TABLE_ID`
- `FEISHU_PHASE2_SPEC_FOOTNOTES_VIEW_ID`
- `FEISHU_PHASE2_SPEC_NOTES_TABLE_ID`
- `FEISHU_PHASE2_SPEC_NOTES_VIEW_ID`
- `FEISHU_PHASE2_SPEC_TITLES_TABLE_ID`
- `FEISHU_PHASE2_SPEC_TITLES_VIEW_ID`
- `FEISHU_PHASE2_SYMBOLS_BLOCKS_TABLE_ID`
- `FEISHU_PHASE2_SYMBOLS_BLOCKS_VIEW_ID`

Execution steps:

1. Collect the Base token plus the 5 table IDs and 5 view IDs from Feishu.
2. Export them in the shell profile used on the new machine.
3. Open a new shell and verify:

```bash
printenv | rg '^FEISHU_PHASE2_'
```

4. Run the repo-level smoke test:

```bash
python3 build.py sync-data --config config.yaml --data-root data/phase2 --dry-run
```

5. If the dry-run passes, run the real sync:

```bash
python3 build.py sync-data --config config.yaml --data-root data/phase2
```

6. Confirm these outputs changed as expected:
   - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
   - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
   - [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
   - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
   - [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
   - [`data/phase2/snapshot_manifest.json`](../data/phase2/snapshot_manifest.json)

Failure triage:

- if `sync-data` fails before any API call, check missing `FEISHU_PHASE2_*`
- if `sync-data` fails on auth, rerun `lark-cli auth status`
- if `sync-data` fails on table access, re-check the specific table/view ID pair

## 4. Part C: Run Parity In A Disposable Worktree

Use a separate Git worktree because `check`, `diff-report`, and `release-manifest` write into tracked output directories under the repo root.
The cleanest no-pollution approach is to let those writes happen in a disposable sibling worktree.

Recommended target:

- config: [`config.yaml`](../config.yaml)
- model: `JE-1000F`
- region: `US`

Execution steps:

1. Create a disposable worktree next to the main repo:

```bash
git worktree add ../auto-manual-parity codex/phase2-feishu-sync
```

2. In that worktree, set up the Python environment and dependencies.
3. Create a scratch folder for captured comparison artifacts:

```bash
mkdir -p .tmp/parity
```

4. Capture the `phase1` baseline:

```bash
python3 build.py rst --config config.yaml --model JE-1000F --region US --source runtime
cp -R docs/_build/JE-1000F/US .tmp/parity/phase1_build
python3 build.py check --config config.yaml --model JE-1000F --region US
python3 build.py release-manifest --config config.yaml --model JE-1000F --region US
```

5. Capture the `phase2` build:

```bash
python3 build.py rst --config config.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
cp -R docs/_build/JE-1000F/US .tmp/parity/phase2_build
python3 build.py check --config config.yaml --model JE-1000F --region US --data-root data/phase2
python3 build.py release-manifest --config config.yaml --model JE-1000F --region US --data-root data/phase2
```

6. Compare the outputs:

```bash
diff -ru .tmp/parity/phase1_build/rst .tmp/parity/phase2_build/rst > .tmp/parity/rst.diff || true
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

## 6. Decision Rule

Do not switch any default config from `phase1` to `phase2` yet.
Only make that change after:

1. `sync-data` is reproducible on the new machine
2. one target parity run is clean
3. any remaining release-manifest or diff-report path-only deltas are understood
