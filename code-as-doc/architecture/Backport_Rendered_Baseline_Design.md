# Backport rendered-baseline design (approach C)

Status: **design / not yet implemented.** Refines the diff foundation of
[`Feishu_Cloud_Doc_Backport_Design.md`](Feishu_Cloud_Doc_Backport_Design.md). The
locate/worktree/route machinery (resolver, `run-review-branch`, sparse worktrees,
F2/F3/F6) already shipped; this doc fixes **what the backport diffs against**.

## 1. The problem (source vs rendered)

`run-review` diffs the fetched cloud-doc against `docs/_review/<model>/<region>/page/*.rst`.
But that file is **RST source** — `.. raw:: latex` directives, `| line-block`
prefixes, `|TOKEN|` substitutions, `**bold**` — while the cloud-doc is the
**rendered** manual (plain text, tokens resolved, no markup). Block-diffing the two
mis-aligns on essentially every block.

Evidence (JE-1000F EU preface; the reviewer made **two** edits — delete the
Ukrainian block + change `IMPORTANT` → `IMPORTANT - test`):

```
old: '| Congratulations on your new Jackery Explorer 1000…'   ← RST line-block source
new: 'Please note that no further notifications…'             ← rendered cloud-doc
```

22 mis-paired "deltas", none of which are the actual edit; a whole-doc run flags
~10 pages. Worse, **applying** rendered text back into the RST corrupts it (a prior
apply stripped `.. raw:: latex \HBApplyLang{en}`). Diffing/applying across two
representations is the root cause — not the locate/scope layer.

## 2. Decision: advancing rendered baseline (C)

Diff in **one representation** by comparing the cloud-doc against a **stored render
baseline**, not the RST source:

- **B (re-render the RST each time):** faithful but the cloud-doc is Feishu-markdown
  export and the build emits docx/HTML — format alignment leaves residual noise.
- **A (normalize both to plain text):** self-contained but lossy on tokens/tables,
  and it still diffs against `_review` every time (no "since last time" notion).
- **C (this doc): baseline = the render that was pushed to the cloud-doc, advanced
  after every backport.** Cleanest isolation (only the reviewer's edits — no markup
  noise, no version drift) **and** it is the only option that handles **repeated
  edits** correctly.

The baseline and the cloud-doc are the **same representation** (both are the Feishu
fetch of the doc), so the diff is fetch-vs-fetch and aligns exactly.

## 3. Repeated edits → the baseline is a moving cursor

```
review start → render R0, push to cloud-doc, store R0 as baseline
edit #1      → cloud = R0+e1 → backport: diff(cloud, R0)=e1 → apply → baseline := cloud
edit #2      → cloud = …+e2  → backport: diff(cloud, baseline)=e2 → apply → baseline := cloud
```

Each run diffs **"now vs the last backport"**, so it captures only the *new* edits;
already-backported edits sit below the cursor and are never re-reported. N edits
across N runs = N clean increments.

## 4. Data model

- **R0 = `fetch(cloud-doc)` taken right after review-start creates the doc.** Taking
  it via the same fetch path future backports use guarantees identical
  representation (no upload-vs-export skew).
- **Baseline store: one file per target+doc, on the review branch**, under a
  build-ignored dir so it never renders or pollutes `page/`:
  `docs/_review/<model>/<region>/.backport/<doc-token>.baseline.md`.
  On-branch = it persists and travels with the branch/PR across machines (BlockClaw
  may run anywhere). The build and review-preview must skip `.backport/`.
- Alternative considered: a dedicated git ref (`refs/backport-baseline/<branch>`) to
  keep it out of the PR. Cleaner history, more git plumbing — deferred; start with
  the on-branch `.backport/` dir.

## 5. Sequence (per backport run)

1. `fetch(cloud-doc)` → `C_now`.
2. Load baseline `B` from `.backport/<doc-token>.baseline.md` on the worktree branch.
   - **No baseline (legacy review / first run):** see §7.
3. `diff(C_now, B)` → reviewer edits (render-vs-render → clean).
4. **Classify** each edit with the existing F2 value-index / F3 family scope:
   Class D → source table (F6) / TM; Class T → template-sync proposal; Class R →
   `docs/_review` prose. (§8.)
5. Apply the **approved** edits via their routed writer (all human-gated as today).
6. **Advance the cursor only if the run fully captured the doc** (§6): write `C_now`
   to `.backport/<doc-token>.baseline.md` and commit it on the review branch
   alongside any `_review` change.

## 6. Un-applied edits must not be lost

If the operator approves only some edits, advancing `B := C_now` would bury the
un-approved ones below the cursor forever. Rule:

- **Advance the baseline only when every reported edit was applied** (or explicitly
  dismissed). On a partial apply, **leave `B` unchanged** — the next run re-diffs
  the same window; already-applied edits are idempotent no-ops (the F6/TM executors
  already skip a delta whose target already holds the new value), so re-reporting is
  safe and nothing is lost.
- Optionally record dismissed `delta_hash`es in `.backport/<doc-token>.dismissed`
  so a deliberately-skipped edit is not re-surfaced every run.

This keeps "advance the cursor" safe: it only moves past a fully-resolved state.

## 7. First run / legacy reviews (no R0)

Reviews that started before this feature have no stored R0. Options, in order:

1. **Going forward:** review-start always stores R0 (§9, phase 1). New reviews are
   clean from edit #1.
2. **Legacy seed:** a `seed-backport-baseline` step fetches the *current* cloud-doc
   and stores it as the baseline **without** applying anything — i.e. it declares
   "treat everything up to now as already-reviewed." Use only when the operator
   confirms there are no pending un-backported edits (else those edits are buried).
3. **One-time fallback:** if neither, the first run may diff against a re-render
   (approach A) just to bootstrap, then store `C_now` so subsequent runs are clean.

Recommend 1 for new reviews and 2 for the existing in-flight ones.

## 8. Tie-in with F2 / F3 / F6 (route to source, not RST)

The clean render-vs-render diff is what finally makes the existing routing work. A
reviewer's edit is rendered text; its real home is usually the **source**, not the
`_review` RST:

- Match the edited text against the **F2 value-index** (`token_resolution_map`,
  rendered value → source row). A hit → **Class D** → write the corrected value to
  the source table (F6) or `Translation_Memory` (the approval-gated writers already
  built). A row regenerates the RST on the next `sync-review`, so we never hand-edit
  rendered text into RST.
- Family-identical across the model family (F3) → **Class T** → template-sync
  proposal.
- No source/template match (genuinely manual review prose) → **Class R** → write the
  `docs/_review` page.

So C does not replace F2/F6 — it **feeds** them a trustworthy delta set. Today they
are starved by a garbage diff.

## 9. Implementation plan (phased)

1. **Store R0 at review-start.** In `process_review_start_queue` (after the doc is
   created/pushed), `fetch(cloud-doc)` once and write
   `docs/_review/<model>/<region>/.backport/<doc-token>.baseline.md`; commit it on
   the seeded review branch. Make the build / review-preview ignore `.backport/`.
2. **Baseline-diff in `run-review-branch`.** When a baseline exists for the resolved
   doc, diff `C_now` against it instead of against the RST page(s); fall back to §7
   when absent. Reuse the existing block parser/differ on the two fetch texts.
3. **Advance the cursor.** On a full apply, write+commit the new baseline (§6);
   on partial, leave it.
4. **Route via F2/F3/F6** (§8) — wire the clean deltas into the existing
   classification + approval-gated writers.
5. **Legacy seed** command (§7.2) + docs (runbook + this design + the parent design's
   R8/baseline section).

Each phase is independently shippable and testable; phase 1+2 already removes the
source-vs-rendered noise, phases 3–4 add incremental + source routing.

## 10. Open decisions (need 夏冰)

- **Baseline storage:** on-branch `.backport/` (recommended, simple, travels) vs a
  dedicated git ref (cleaner PR history). 
- **What counts as "fully captured" for cursor advance** (§6): all-applied-only
  (recommended) vs always-advance-with-pending-list.
- **Legacy in-flight reviews:** seed-now (§7.2) vs let the first run bootstrap (§7.3).
