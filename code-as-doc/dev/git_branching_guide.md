# Git Branching Guide

Updated: 2026-03-23

Use this file for the current Git branching, pull request, merge, tag, and GitHub branch protection rules for this repo.

This guide complements:

- [`AGENTS.md`](../../AGENTS.md)
- [`../build_doc_guide.md`](../build_doc_guide.md)
- [`code_review_checklist.md`](code_review_checklist.md)
- [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

## 1. Default Model

This repo should use trunk-based development.

Current rule:

- `main` is the only normal long-lived branch.
- `main` should stay releasable.
- All normal work should start from `main` and return to `main` through a pull request.
- Prefer short-lived topic branches.
- Do not use long-lived branch lanes such as language branches, demo branches, personal branches, or versioned draft branches as the normal workflow.

Why this repo uses this model:

- the repo tracks shared templates, phase1 CSV data, target review bundles, and Git-visible generated RST
- long-lived branches make `_review` and Git-visible generated files drift quickly
- merge cost rises fast when shared logic and target review content move on separate long-running branches

## 2. Allowed Branch Types

Use one of these branch families.

- `feat/<area>-<topic>`
  - new user-visible behavior
  - new build capability
  - new data-driven manual behavior
- `fix/<area>-<topic>`
  - bug fix
  - regression fix
  - release blocker fix
- `refactor/<area>-<topic>`
  - code movement
  - decomposition
  - maintainability cleanup without intentional behavior change
- `docs/<topic>`
  - documentation-only changes
- `chore/<topic>`
  - repo maintenance
  - CI, metadata, or housekeeping
- `review/<MODEL>-<REGION>-<topic>`
  - target-specific review editing after review has started
  - target-specific release polish
- `spike/<topic>`
  - time-boxed investigation or prototype
  - not intended to live long or merge as-is
- `release/<MODEL>-<REGION>-<yyyymmdd>`
  - exception-only branch for release freeze or controlled hotfix work
  - not part of the daily workflow

Naming rules:

- use lowercase for the branch family and topic
- use `-` to separate words inside the topic
- include `<MODEL>-<REGION>` only when the branch is target-specific
- keep `<MODEL>` and `<REGION>` in the repo's canonical target form, usually uppercase
- keep one branch focused on one purpose
- do not create one branch per model only because the model changed
- do not encode author names or draft versions into the normal branch pattern

Examples:

- `feat/draft-engine-manifest`
- `fix/check-stale-identity-scan`
- `refactor/build-routing-split`
- `docs/git-branching-guide`
- `review/JE-1000F-US-safety-pass2`
- `release/JE-1000F-JP-20260322`

## 3. Which Branch To Use

Use `feat/*`, `fix/*`, or `refactor/*` when the change belongs to shared code, templates, config families, phase1 CSV rules, review tooling, validation, or release tooling.

Use `review/<MODEL>-<REGION>-<topic>` when the change is mainly target-specific content under [`docs/_review/<model>/<region>/`](../../docs/_review) or a tightly related target-specific output refresh.

Use `docs/*` when the change is documentation-only and does not intentionally change repo behavior.

Use `spike/*` only for investigation. If the spike proves useful, start a clean `feat/*`, `fix/*`, or `refactor/*` branch from `main` and carry over only the parts that should survive.

Use `release/*` only when an explicit release freeze or post-release hotfix needs a temporary stabilization lane. Normal publishing should happen from `main`.

## 4. Standard Daily Workflow

### 4.1 Start From Updated Main

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/draft-engine-manifest
```

### 4.2 Keep The Scope Small

One branch should usually cover one of these:

- one shared behavior change
- one bug fix
- one target review pass
- one docs-only change

If shared logic and target review text can be separated, open two pull requests instead of one large mixed branch.

### 4.3 Sync With Main Early

If a branch stays open for more than a day or two, rebase it on top of current `main` before review:

```powershell
git fetch origin
git rebase origin/main
```

If multiple people are already pushing to the same branch, coordinate before rewriting history.

### 4.4 Validate Before Opening A Pull Request

Use both personal validation and machine validation.

Personal validation means the checks you run locally before opening or updating a pull request.
Machine validation means the GitHub `Manual Validation` workflow that must pass before merge.

Use the local validation set that matches the change.

- logic changes: `python -m unittest`
- build or quality-gate changes: `python build.py check --config config.yaml --model JE-1000F --region US`
- JP review or publish changes: `python build.py publish --config config.ja.yaml --model JE-1000F --region JP`
- diff-report changes: `python build.py diff-report --config config.yaml --model JE-1000F --region US`
- release traceability changes: `python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP`
- docs-only changes: self-review links, paths, examples, and command accuracy

Do not open a pull request with unreviewed generated `html`, `word`, or `pdf` outputs.

Current rule:

- personal validation happens first on the branch owner machine
- machine validation happens in GitHub on the pull request
- `main` should only accept changes that passed the required machine validation checks

### 4.5 Open A Pull Request To Main

Pull request rules:

- base branch: `main`
- keep the title specific and readable
- explain which surfaces changed: code, templates, CSV, `_review`, Git-visible `_build`, reports, or docs
- call out why `_review` or Git-visible `_build/.../rst/**` files changed
- call out if `review --refresh-review` was used intentionally
- include the validation commands you actually ran

### 4.6 Merge And Clean Up

Normal merge rule:

- use `Squash and merge`
- delete the head branch after merge
- do not keep the branch alive as a second working lane after merge

## 5. Repo-Specific Content Rules

This repo has Git-visible review and generated surfaces, so branch discipline matters more than in a code-only repo.

Current rules:

- [`docs/_review/<model>/<region>/`](../../docs/_review) is the durable editing surface after review starts
- a `review/*` branch should usually touch one target only
- shared fixes for templates, CSV, or tooling should happen on `feat/*`, `fix/*`, or `refactor/*`, not on a long-lived review branch
- [`docs/_build/<model>/<region>/rst/**`](../../docs/_build) may be committed only when the generated RST is intentionally part of the reviewed change
- `html/**`, `word/**`, and `pdf/**` outputs remain build artifacts and should not be committed as part of normal pull requests
- avoid mixing large generated churn with unrelated refactors in the same branch
- do not delete or rewrite user verification artifacts under `_build`, `reports/version_tracking`, or `reports/releases` unless the task explicitly requires cleanup

## 6. Commit And Pull Request Conventions

Prefer meaningful commit subjects instead of repeated `update`.

Recommended commit format:

- `feat(manual): add manifest-based draft generation`
- `fix(check): catch stale foreign model names`
- `refactor(build): split target resolution helpers`
- `docs(git): add branching and protection guide`

Recommended pull request title format:

- `feat(manual): add US symbols review flow`
- `fix(word): correct JP safety list indentation`
- `docs(repo): define Git branching policy`

If a branch grows past one clear purpose, split it before merge.

## 7. Release And Tag Rules

Normal release flow:

- merge the final approved change to `main`
- run the formal publish flow from `main`
- tag the release commit

Recommended tag patterns:

- `manual-<MODEL>-<REGION>-<yyyymmdd>`
- `manual-<MODEL>-<REGION>-<yyyymmdd>-r2`

Examples:

- `manual-JE-1000F-US-20260322`
- `manual-JE-1000F-JP-20260322-r2`

Use `release/<MODEL>-<REGION>-<yyyymmdd>` only when all of these are true:

- a release needs a temporary freeze branch
- only release-blocking changes should enter
- the branch will be merged back to `main` immediately after release or hotfix completion

## 8. GitHub Branch Protection Checklist

Apply these settings to the `main` branch.

If your GitHub plan supports rulesets, create a ruleset targeting `main`.
If you use legacy branch protection, create the equivalent branch protection rule for `main`.

### 8.1 Main Branch Rule

- Target branch: `main`
- Require a pull request before merging: `ON`
- Required approvals: `0` for the current single-maintainer workflow
- Dismiss stale pull request approvals when new commits are pushed: `ON`
- Require approval of the most recent reviewable push: `OFF` for the current single-maintainer workflow
- Require conversation resolution before merging: `ON`
- Require status checks to pass before merging: `ON`
- Require branches to be up to date before merging: `ON`
- Required status checks:
  - `Manual Validation / unit (pull_request)`
  - `Manual Validation / doctor-en (pull_request)`
  - `Manual Validation / check-en (pull_request)`
  - `Manual Validation / check-jp (pull_request)`
  - `Manual Validation / check-eu (pull_request)`
- Require linear history: `ON`
- Allow force pushes: `OFF`
- Allow deletions: `OFF`
- Lock branch: `OFF`
- Restrict who can push to matching branches: `OFF` for normal contributors if pull requests are already required
- Bypass list: keep empty if possible; if your team needs an emergency path, limit bypass to a very small maintainer set and document who owns that responsibility

Current CI binding rule:

- GitHub `Manual Validation` is the required machine-validation workflow
- pull requests run the merge-gating checks
- pushes to `main` run the same workflow again after merge for post-merge validation
- feature branches should not depend on a second duplicate GitHub `push` validation run

If the repo later becomes a real multi-maintainer repo, revisit these two settings:

- Required approvals: move from `0` to `1`
- Require approval of the most recent reviewable push: move from `OFF` to `ON`

### 8.2 Optional Release Branch Rule

Only add this if the repo starts using temporary `release/*` branches.

- Target branch pattern: `release/*`
- Require a pull request before merging: `ON`
- Required approvals: `1`
- Dismiss stale approvals: `ON`
- Require conversation resolution: `ON`
- Require status checks to pass before merging: `ON`
- Require linear history: `ON`
- Allow force pushes: `OFF`
- Allow deletions: `OFF`

### 8.3 Adjacent GitHub Repository Settings

These are not branch protection toggles, but they should match this policy.

- Default branch: `main`
- Allow squash merging: `ON`
- Allow merge commits: `OFF`
- Allow rebase merging: `OFF`
- Automatically delete head branches: `ON`

If your team later adopts `CODEOWNERS`, turn on `Require review from Code Owners` for `main`.

### 8.4 Status Check Troubleshooting

If a pull request shows successful GitHub Actions runs but the merge box still says `Expected — Waiting for status to be reported`:

- first confirm there is no legacy rule under `Settings -> Branches`
- then open the active `Protect main` ruleset under `Settings -> Rules`
- remove the required checks and add them again from the latest successful pull request run
- prefer the exact `Manual Validation / ... (pull_request)` check names
- refresh the pull request page after saving the ruleset

Typical cause:

- the ruleset is still bound to an older required-check context after workflow or branch-protection changes

## 9. Migration Rule For The Current Repo

When cleaning up the current branch landscape:

- merge active work back to `main` in small pull requests
- stop using versioned draft branches as long-lived lanes
- retire stale experimental branches after the useful work is merged or intentionally abandoned
- do not create new long-lived branches that duplicate `main` plus a theme such as language, demo, or strategy

## 10. One-Sentence Summary

Use `main` as the only normal long-lived branch, do all daily work on short-lived topic branches, merge through reviewed squash PRs, and protect `main` with required checks plus no-force-push rules.
