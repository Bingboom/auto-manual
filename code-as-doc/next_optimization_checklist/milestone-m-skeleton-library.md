# Optimization checklist: Milestone M (skeleton library expansion)

Part of the [optimization checklist](../next_optimization_checklist.md); its index lists every milestone page,
and its §1 update rules apply here. Update item status on this page and add new
items for this milestone here, not to the hub.

## 6k. Milestone M: Skeleton Library Expansion (骨架库产线拓展)

Registered 2026-08-21 from the Phase A corpus audit
([`architecture/manual_ia_audit_2026-08.md`](../architecture/manual_ia_audit_2026-08.md)),
the Phase B design
([`architecture/Product_Skeleton_Library_Design.md`](../architecture/Product_Skeleton_Library_Design.md))
and the wave plan
([`dev/skeleton_library_expansion_plan.md`](../dev/skeleton_library_expansion_plan.md)).
This milestone is the **superset execution** of Workstream M (`page_registry`
becomes the only composition authority) in
[`optimization_project.md`](../optimization_project.md).

Milestone status: `in_progress` — the S1–S6 vertical slice is done: S1 #936 (`1823cc4e`),
S2 #937 (`eeb8eaa8`), S3 #938 (`71f7c5ec`), S4 #940 (`5e1d0c26`) and
S5 #939 (`0432e5b7`). Both S4 source-table batches have landed, and #944
(`baf8b712`) restored the JBP target from CI `SKIP` to `PASS`. S6 closed
2026-08-30 after the shared-component target assembly, pipeline-side
reconciliation, native InDesign preflight, 28-page visual comparison,
self-contained delivery-pack checks and operator ruling were all recorded.
The milestone remains `in_progress` because the post-slice rollout and the
remaining milestone exit criteria below are still open.
Milestone entry gate: operator approves the **vertical slice plan** (the wave
plan's v2). S1 may start on that approval alone; every later slice item has
its own gate.

> **This section was rewritten 2026-08-21 after an executability audit.** The
> first draft was written from the design documents without checking the live
> repo and carried 19 substantive defects — including one that would have
> reverted a shipped fix. Every claim below has been re-verified against code.
> Where a condition is *not* verifiable today, it now says so instead of
> implying a check exists.

**Baseline being changed** (measured): corpus 58 independent manuals,
**15 buildable (25.9%)**, SKU coverage 5/22, battery-pack category 0%, JP the
largest queue at 18 manuals with 1 buildable; reconstruction 47/58 pure
deletion (81.0%) / 55/58 with ≤1 overlay (94.8%).

**Premise (operator, 2026-08-21):** a shipped book is **pipeline output + an
InDesign finishing layer**. A template-zero-hit block is hand-placed at layout
time, not unprintable. Never report a finishing-layer item as a production
blocker.

### M-pre. Cross-cutting rules — apply to every PR in this milestone

These were the largest gap in the first draft: each was missing from the
individual items, and each will fail CI or damage a live line if skipped.

1. **Any PR touching `configs/**` or `docs/manifests/**` must regenerate the
   family diff carriers.** `.github/workflows/manifest-regenerate-diff.yml`
   runs `python tools/manifest_family.py fold` (no `--write`), and
   `fold_repository` requires `rebuilt == YAML golden` for every indexed entry.
   `manual_jp.yaml`, `manual_zh.yaml` and `manual_eu.yaml` all have carriers.
   - the all-pairs command is **`fold`**, not `roundtrip` — `roundtrip` requires
     `--base` and `--target` and compares exactly one pair
   - since S1 (#936) `fold` reports `manifest_count: 18, anchor_count: 3,
     folded_count: 15, passed: true` (re-measured 2026-08-21); the third
     anchor is `docs/manifests/manual_bp-us.yaml`
2. **Any new manifest must be registered in
   [`../docs/manifests/family/index.yaml`](../../docs/manifests/family/index.yaml)
   in the same PR.** `fold_repository` globs `docs/manifests/*.yaml` and reports
   `manifest is not in the family index` for orphans, failing the run. The
   hardcoded counts in
   [`../tests/test_manifest_family.py`](../../tests/test_manifest_family.py) must
   be updated in the same PR — S1 (#936) already moved them from `17/2/15` to
   `18/3/15`, so the next new manifest starts from there.
3. **Any PR that changes materialized page names touches committed review
   derivatives.** `docs/_review/JE-1000F/US/page/` tracks **52** files on
   `main`, **22** of them real `pNN_` names, and
   `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json`
   (status `approved`) pins names like `p20_01_user_maintenance_instructions`.
   Live review branches pin more, and they live on the **Hello-Docs mirror
   remote**, not on this repo's `origin`: `hello-docs/review/JE-300E-EU`
   carries 185 derivative files — 109 under `JE-300E/EU` and 76 under
   `JE-1000F/US`, i.e. more JE-1000F pins than `main` itself holds.
   **AGENTS.md §8.7 requires operator confirmation before deleting or renaming
   committed `docs/_review/**` files** — so name-changing PRs carry that gate
   explicitly, and the reference-layout contract pin must be re-approved, not
   silently updated (the #720/#724 lesson).
4. **Golden conservation is proven by two detached worktrees at base and head
   SHA — not by `git stash` and not by `git diff docs/_build`.** Operator
   review 2026-08-21: `git stash` does not remove *committed* changes and skips
   untracked files by default, so a stash-based "before" can already contain
   the very PR under test. And the tracked `docs/_build` snapshot has drifted
   (234 files, JE-1000F US/JP only; assembly `rmtree`s the tree), so its git
   diff is noise. Use:
   ```
   git worktree add /tmp/m-base <base-sha>
   git worktree add /tmp/m-head <head-sha>
   (cd /tmp/m-base && python3 build.py check --config <cfg> --model <M> --region <R> --staging-root /tmp/out-base)
   (cd /tmp/m-head && python3 build.py check --config <cfg> --model <M> --region <R> --staging-root /tmp/out-head)
   diff -r /tmp/out-base/docs/_build /tmp/out-head/docs/_build   # must be empty
   git worktree remove /tmp/m-base && git worktree remove /tmp/m-head
   ```
   Each worktree contains exactly its committed tree, so before/after stay
   unambiguous even with local uncommitted or untracked files present. Three
   traps measured while actually running this (S1 #936, S5 #939):
   - a fresh worktree has **no `data/phase2`** (gitignored local mirror), so
     every build in it dies at identity resolution. `cp -R data/phase2
     /tmp/m-base/data/` in each worktree before the check
   - `--staging-root` is for `check` only. `build.py all`'s HTML step runs
     Sphinx, whose extensions require the owning repository tools package, so
     a staging root outside the repo fails with `hb_latex_callouts requires
     the owning repository tools package`. Full-stack builds happen **inside**
     the worktree
   - an in-checkout `build.py check` can leave tracked `docs/_review`
     generated drafts dirty **even with `--staging-root`**; the
     derived-surface-guard hook catches it. Restore before running
     content-pinned suites (`test_web_presentation` reads those files)
5. **New RST templates and fragments need a declared content provenance.** The
   corpus is PDFs outside the repo
   (`~/Downloads/信息架构分析/{便携主机,便携加电包}/`); RST needs text. For each
   new template the PR states: extraction source (which manual, which printed
   page), who reviews the wording, and — for legal text — who signs off. Do not
   let an executor invent legal copy.
6. **Every PR states its rollback.** Follow the design's S0–S4 pattern: prefer
   changes that are revertible by one `git revert`; for anything that is not
   (schema changes, file deletions, page renames), name the restore procedure in
   the PR body before merging.
7. **Known-red baselines must be recorded, not discovered.** On today's clean
   tree, `build.py check --config configs/config.zh.yaml --model JE-2000E
   --region CN` **fails** with `UNUSED_FOOTNOTE … 'ac_bypass'` from
   `data/phase2/Spec_Footnotes.csv:2` (re-measured 2026-08-21: still exactly
   1 issue). `us-en/JE-1000F_US`, `ja/JE-1000F_JP`, `eu/JE-1000F_EU`,
   `eu/JE-300E_EU` and `pt-br/JE-1000F_pt-BR` are all green. The slice adds a
   second recorded red, and it MOVED once already — record the date with the
   number or it will mislead. Pre-intake (2026-08-21, #940 tree):
   `bp-us/JBP-2000B_US` failed with exactly 30 `MISSING_REQUIRED_SPEC_ROW`
   issues, zero contract and zero template issues. Post-intake (2026-08-22,
   first batch landed): `validate_spec_master` is **OK**, and the red moves
   downstream to `symbols page has no matching rows sku= lang=en` — the
   `csv_page` batch the intake order defers. The `sku=` there is a red
   herring: `sku` is empty for **every** `--model` build including the
   JE-1000F/US one that ships today, and an empty `sku` makes `_scope_allows`
   permissive, so it can never cause a no-match. An executor must never
   mistake a pre-existing red for their own breakage.

### Post-S6 rollout backlog (full audited text in commit 80321368)

S6 is accepted. Every item below remains deferred until it is re-scoped against
the final S6 report and its own M-pre gate is satisfied.

- [ ] M0 ordinal/naming decoupling for **existing** manifests — `deferred`;
  the slice proves slot_id naming on new manifests only; migrating the pNN_
  world stays gated on M-pre.3 (committed review derivatives + approved pin).
- [ ] M1 language-block parameterization of the 17 existing manifests +
  family index v2 — `deferred`; the slice's resolver is the prototype.
- [ ] M2 App/联网 capability — `deferred`, **blocked on a design decision**
  (no blank state exists: writer emits TRUE/FALSE only, empty reads as FALSE
  and drops the page everywhere).
- [ ] M3 `MAIN@JP` opening repair — `deferred`; must be an in-place
  restructure of `01_meaning_of_symbols.rst` (adding `safety_ja.rst` back
  would revert #607; it is a byte-exact 64-line prefix).
- [ ] M4 `MAIN@CN` repair + conformity tail slot — `deferred`; note the
  known-red `JE-2000E/CN` baseline (`ac_bypass` UNUSED_FOOTNOTE).
- [ ] M5 full BP family (EU 6-language as slice #2, JP cell, A5 dissolution)
  — `deferred`; both `target_defaults` failure paths must be closed for any
  JP-family config.
- [ ] M7 full contract tiering + JE-300E fork reclamation (7 assets, 6
  manifests' model_overrides, 5 diff carriers, AC presence bits) — `deferred`;
  gate on M5-equivalent category data and the live `review/JE-300E-EU` branch.
- [ ] M6 `page_registry` composition authority — `deferred`; hard-gated on
  truthful manifests (M3/M4) and T-K4.
- [ ] M8 compliance fragment library + Row_key/Variant_key split — `deferred`;
  operator compliance decision table signs first; ANATEL is a finishing-layer
  item, not a blocker.
- [ ] M9 data-quality closeout + PH line + reverse-gap registration —
  `deferred`; requires a PH manifest, not just a config; no dependency on M5.

### Milestone M exit criteria (unchanged targets, slice-first path)

- [x] slice S1–S6 accepted, reconciliation report ruled on
- [ ] rollout re-scoped from the report and executed
- [ ] all five skeleton cells build at least one target end to end
- [ ] corpus reconstruction 58/58 (3 outliers registered `legacy`)
- [ ] **HTE153 regression-baseline reconciliation** (AU/KR/pt-BR pipeline
      output vs shipped books)
- [ ] **the Workstream W field test**: next real new line ≤2 operator days
- [ ] known-red baselines fixed or re-recorded; maintenance record appended to
      [`code_optimization_log.md`](../code_optimization_log.md); Workstream M
      status updated in [`optimization_project.md`](../optimization_project.md)
