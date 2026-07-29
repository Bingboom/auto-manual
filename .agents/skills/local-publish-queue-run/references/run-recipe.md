# Local publish-queue run recipe

Grounded in the 2026-07-09 JE-1000F_JP/US local publishes and the 2026-07-21
eleven-attempt publish repair (K7 supply). The env inventory mirrors
`.github/workflows/feishu-build-queue.yml` (the `env:` block of the
`process-queue` job) — when that block changes, update this file in the same
change.

## 1. Env assembly (bot identity)

- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` — from the operator via clipboard
  (`pbpaste`); export into the shell, mask in any echo.
- `FEISHU_PHASE2_IDENTITY=bot` — lark-cli defaults to the user identity;
  this makes the run identical to CI's bot.
- The full `FEISHU_PHASE2_*` set from the workflow env block:
  `FEISHU_PHASE2_BASE_TOKEN`, then TABLE_ID (+ VIEW_ID) pairs for
  spec rows source, page placeholders source, spec footnotes, spec notes,
  symbols blocks, LCD icons, troubleshooting, variable defaults, variable
  lang overrides, manual copy source, document link, model capabilities;
  plus `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` / `_TABLE_ID` / `_VIEW_ID`.
  **sync-data's preflight requires EVERY source-table view id non-empty** —
  use each table's unfiltered full view.
- Wiki destinations (two different secrets — do not swap them):
  - `FEISHU_REVIEW_DOC_WIKI_NODE` = 过程文档管理 node
    (`AvBhwdpNxivgXfkPm1VcCG01nPh`) — where review/baseline **cloud docs**
    land.
  - `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN` — **leave empty**: Word
    files then default to the 文档构建 base node, which is correct. Setting
    it once misfiled Word files into 过程文档管理.
- `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=lark_drive`.

## 2. Local git-plane alignment

- `git branch -f main origin/main` before running — the queue's
  `prepare_git_ref_worktree` prefers **local** branches, and this repo's root
  checkout habitually sits on an operator branch; an orchestrator that is new
  does not make the *build plane* new.
- `data/phase2/` is an untracked local mirror: when starting from a fresh
  worktree, copy it in, or `validate_spec_master` fails with
  `MISSING_SPEC_MASTER`.

## 3. Queue-row operations

Rows live in the build table (document_link, `tblbnRHjpJeCVTtj`, business
plane). Facts that cost real time:

- **Only the row's `Git_ref` field selects the built ref** — there is no
  working CLI override. To build different content: point the row's ref, or
  `git branch -f review/<target> <sha>` locally (the queue uses local
  branches) and restore it after the test.
- **Re-running a consumed row:** `是否触发文档构建` is a select (`Y` /
  `已构建`); `--record-id` refuses an already-built row. Flip it back:

  ```bash
  lark-cli base +record-batch-update --base-token <BASE> --table-id tblbnRHjpJeCVTtj \
    --json '{"record_id_list":["<rid>"],"patch":{"是否触发文档构建":["Y"]}}'
  ```

- **`data_sync=refreshed` makes a re-run skip the phase2 sync** → a fresh
  worktree then misses `Spec_Master.csv`. Also tick the checkbox
  `是否强制刷新数据` (true) when re-triggering.
- Remote alternative when CI is available: dispatch the matching mirror
  workflow, e.g.
  `gh workflow run feishu-draft-build-queue.yml --repo Bingboom/Hello-Docs -f queue_record_id=<rid>`
  (publish counterpart: `feishu-build-queue.yml`; seeding: `feishu-start-review.yml`).

## 4. Run (CI-identical)

```bash
PYTHONUNBUFFERED=1 python -u build.py process-build-queue \
  --config configs/config.us.yaml --data-root data/phase2 \
  --workflow-action publish [--record-id <rid>] [--dry-run]
```

- The command shape is exactly CI's (`feishu-build-queue.yml` "Process Feishu
  build queue" step); `--workflow-action` also accepts `build-draft-package`.
- `PYTHONUNBUFFERED=1 python -u` — orchestrator stdout is buffered and
  arrives scrambled otherwise; diagnosis needs ordered logs.

## 5. Verify — all three, every run

1. **Artifacts on disk**: `reports/releases/<model>/<region>/...` including
   `publish_meta.json` (carries `handoff_package_path`).
2. **Knowledge-base upload**: review/baseline cloud docs under 过程文档管理;
   the Word-file link written to the row's `Document link`.
3. **Row write-back**: `idml_file` (wiki URL) and status fields updated on
   the queue row — read the row back. `processed=1 failed=0` in the summary.

## 6. Delivery (IDML handoff zip)

- Publish delivers a **handoff zip**, not a bare `.idml`: `tools/idml/
  delivery.py` post-processes (collects linked resources into `Links/`,
  relativizes `LinkResourceURI`, repacks with a self-check).
- Fonts are **opt-in**: the repo tracks zero font binaries (Gilroy is a
  commercial license). Set `AUTO_MANUAL_LOCAL_GILROY_DIR` to a local font dir
  to include `Document fonts/`; CI ships only the fonts manifest.
- Local iteration builds: name the zip with a `LOCAL` marker so it can never
  be mistaken for a released artifact.

## 7. Second-host acceptance (K7)

- Follow `code-as-doc/dev/indesign_second_host_runbook.md` (§2 is the
  acceptance run). Version pin: `tools/idml/indesign_version_pin.json` —
  finalize refuses on InDesign version mismatch; `--allow-version-mismatch`
  records the override into the report's toolchain block.
- **Acceptance semantics: the second host's finalize report matches the
  primary host's baseline report item-for-item** (overset ids/order, page
  frames; path-stripped JSON diff = 0). It is NOT "overset = 0" — known
  overset items are designer work items by design (drag-to-reveal), and the
  primary baseline carries them too.

## 8. Failure-triage index (symptom → first place to look)

| Symptom | First look |
| --- | --- |
| sync-data preflight rejects | a source-table VIEW_ID is empty (env §1) |
| `MISSING_SPEC_MASTER` | phase2 mirror not copied in, or `data_sync=refreshed` skip (§2/§3) |
| queue resolves no config / wrong target | row `Lang`/region fields; config family match |
| LaTeX/publish-only crash on a review branch | de-templated review pages (raw `tabular`, `.svg` images, prose outside `\safetywarning{}`) — Word-stage review can't see LaTeX-only breakage |
| asset resolves to the wrong bytes | three same-name sources (shared / override / review overlay) — byte-level winner rules; check `docs/_review` overlays |
| reference/parity contract gate refuses | approved-plan mismatch — STOP; rebind is operator-approved, never `--write` around it |
| CI queued forever | org Actions quota exhausted — this local lane is the workaround |
