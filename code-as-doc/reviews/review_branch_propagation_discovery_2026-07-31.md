# Review-Branch Propagation Discovery — 2026-07-31

## Scope

This discovery supports Workstream V / K15 and Workstream W Stage 5 item 14.
It records the live branch topology and the current protection mechanisms before
the propagation design is approved. It makes no runtime or branch mutation.

## Live inventory

The authoritative `origin` currently exposes 15 `review/*` branches, and each
has an open pull request into `main`.

- 14 branches have unique file changes exclusively under `docs/_review/**`.
- `review/JE-1000F-US` also carries four historical generated images under
  `docs/_build/**`; those are migration debt, not a pattern to preserve.
- Branches are 295–624 commits behind current `main` and one to four commits
  ahead of their merge base.
- Four legacy `review/id-*` branches overlap named product/region branches.
  The live queue's `Git_ref` must decide which branch is canonical; branch
  names alone are not enough evidence to delete or merge a duplicate.

This is already close to the desired derivative-only ownership boundary, but
the branches have no machine-enforced shared-source cursor. Their review
manifest records the seed-time `git_sha`; it does not say which shared source
was last safely propagated or whether the data snapshot needed to reproduce
that derivative is retrievable.

## Current mechanics

- `tools/check_review_branch_sync.py` notices shared template/manifest edits,
  lists likely affected review branches, and exits successfully by default. It
  does not create a bump plan or PR.
- Its default remote is `hello-docs`, while this checkout has only `origin`.
  The check therefore reports an unreachable remote unless the operator passes
  the actual remote explicitly. A future inventory must make the repository
  source explicit and fail visibly when it cannot enumerate branches.
- Review start builds from a selected `main` base and writes a full frozen
  derivative under `docs/_review/<model>/<region>[/<lang>]`.
- Queue review builds currently use the latest trusted `origin/main` toolchain
  and overlay review content from `Git_ref`. This decouples executable code from
  review content, but it does not materialize shared templates from a recorded
  pin.
- `sync-review` has two update modes: whole-file `copy` and placeholder-aware
  `merge_params`. The latter preserves most authored prose, but the current
  warning is accurate: a reviewer edit on the same placeholder-bearing line can
  be overwritten. It is not sufficient evidence for unattended propagation.
- `sync_preserve_paths` is an explicit hard-preserve list and must remain a hard
  abstention signal.
- Cloud-doc backport already applies the complementary reverse-direction rule:
  resolve to the review derivative, classify source ownership, and abstain when
  the destination cannot be proven.

## Safety conclusions

1. Do not rebase or force-refresh open review branches to propagate `main`.
2. Store a shared-source commit pin inside each target's review metadata; do not
   use branch ancestry as that pin.
3. Generate a three-way comparison from reproducible inputs:
   old unreviewed derivative, current authored derivative, and candidate new
   unreviewed derivative.
4. Automatically apply only classifications proven disjoint from authored
   edits. Any overlap, missing baseline, missing snapshot, rename, or ambiguous
   page mapping must abstain and stay visible.
5. Advance the pin only through a target-specific bump PR with rendered before
   and after evidence.
6. Migrate one live family first. Existing branches remain buildable under the
   current path until individually adopted.

The detailed contract and rollout are specified in
[`../architecture/Review_Branch_Propagation_Design.md`](../architecture/Review_Branch_Propagation_Design.md).
