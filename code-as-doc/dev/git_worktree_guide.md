# Git Worktree Guide

Updated: 2026-04-21

Use this file for the current local `git worktree` workflow in this repo.
It explains how to create a worktree from a branch, where to put it on disk, how to rename or remove it safely, and how to avoid the common Windows errors we hit in daily use.

This guide complements:

- [`AGENTS.md`](../../AGENTS.md)
- [`git_branching_guide.md`](./git_branching_guide.md)
- [`../build_doc_guide.md`](../build_doc_guide.md)
- [`../../user-guide/hello_auto-doc.md`](../../user-guide/hello_auto-doc.md)

## 1. When To Use Worktrees

Use a worktree when you need more than one checked-out branch on the same machine at the same time.

Typical cases in this repo:

- keep `main` open in the primary repo root
- open one review branch for JP and another review branch for US in parallel
- isolate target-specific `_review` or `_build` work without switching the main checkout back and forth
- compare two review branches side by side in VS Code

Do not use a second worktree just because the branch name changed once.
Treat worktrees as disposable local workspaces, not as a second long-lived branch model.

## 2. Recommended Local Layout

On Windows, prefer a path under the current signed-in user account instead of another user's home directory.

Recommended root:

```powershell
C:\Users\<you>\Documents\cms2docs\worktrees
```

Examples:

```powershell
C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP
C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-US
```

Why this layout is recommended:

- it avoids permission problems from paths under another user such as `C:\Users\tangxb\...`
- it keeps throwaway review workspaces out of the main repo root
- it gives the folder a readable task name, which also becomes the practical "workspace name" in Explorer and VS Code

## 3. Before You Create One

Check these points first:

- run `git worktree list` so you know which branches are already attached elsewhere
- remember that one branch can only be checked out in one worktree at a time
- create the target parent directory first if it does not already exist
- keep the worktree path under a location you can write to

Current repo safety note:

- this repo may generate files under `_build`, `reports/version_tracking`, and `reports/releases`
- before deleting a worktree with `--force`, make sure you do not still need local review edits or verification artifacts inside that directory

## 4. Create A Worktree From An Existing Local Branch

If the branch already exists locally, the flow is:

```powershell
New-Item -ItemType Directory -Force `
  C:\Users\Administrator\Documents\cms2docs\worktrees

git worktree add `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-US `
  review/JE-1000F-US
```

That command:

- creates a new directory for the worktree
- checks out the target branch in that directory
- keeps the main repo root on its current branch

## 5. Create A Worktree When The Branch Exists Only On Origin

If the branch exists on `origin` but not as a local branch yet, create a local tracking branch first, then attach the worktree.

```powershell
git fetch origin

git branch --track `
  review/JE-1000F-JP `
  origin/review/JE-1000F-JP

git worktree add `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP `
  review/JE-1000F-JP
```

Use this flow when `git show-ref --verify refs/heads/<branch>` fails locally but `origin/<branch>` exists.

## 6. Repo Example

The current repo examples we used are:

```powershell
New-Item -ItemType Directory -Force `
  C:\Users\Administrator\Documents\cms2docs\worktrees

git branch --track `
  review/JE-1000F-JP `
  origin/review/JE-1000F-JP

git worktree add `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP `
  review/JE-1000F-JP

git worktree add `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-US `
  review/JE-1000F-US
```

After creation, confirm with:

```powershell
git worktree list -v
```

## 7. Daily Use

Useful commands:

```powershell
git worktree list
git -C C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP status
git -C C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-US status
```

Open one worktree directly in VS Code:

```powershell
code C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP
```

Open several folders into one VS Code multi-root workspace if you want to compare branches side by side.

## 8. Rename Or Move A Worktree

There is no separate Git-level "worktree display name".
In practice, the worktree name is the folder name.
To rename a worktree, move it to a new path:

```powershell
git worktree move `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP `
  C:\Users\Administrator\Documents\cms2docs\worktrees\jp-review
```

If you moved the folder manually in Explorer and Git's metadata still points at the old path, repair it with:

```powershell
git worktree repair `
  C:\Users\Administrator\Documents\cms2docs\worktrees\jp-review
```

Windows note:

- if `git worktree move` fails with `Permission denied`, first confirm the target parent directory exists
- then close terminals, VS Code windows, or Explorer windows that are holding the source folder open

## 9. Remove A Worktree

If the worktree is clean:

```powershell
git worktree remove `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP
```

If the worktree has local changes and you intentionally want to discard them:

```powershell
git worktree remove --force `
  C:\Users\Administrator\Documents\cms2docs\worktrees\review-JE-1000F-JP
```

After removing stale directories or broken metadata, clean up registrations with:

```powershell
git worktree prune -v
```

## 10. Common Errors

### 10.1 Branch Already Used By Another Worktree

Example:

```text
fatal: 'review/JE-1000F-US' is already used by worktree at '...'
```

Meaning:

- the same branch is already checked out in another worktree

Fix:

- reuse that existing worktree
- move that existing worktree with `git worktree move`
- remove that existing worktree if it is no longer needed
- or create a different branch if you truly need a second parallel checkout

### 10.2 Permission Denied During Move

Typical causes:

- the target parent directory does not exist
- the target path is under another user's home directory
- some app still holds the source directory open

Fix:

- create the parent directory first
- move the worktree under your own user path
- close VS Code, terminals, and Explorer windows that point at that worktree

### 10.3 VS Code Shows `UNTITLED (WORKSPACE)`

That label is a VS Code multi-root workspace name, not a Git worktree name.

If you opened multiple folders such as:

- `auto-manual`
- `review-JE-1000F-JP`
- `review-JE-1000F-US`

then VS Code creates a temporary unnamed workspace.
To name it:

1. Use `File`
2. Use `Save Workspace As...`
3. Save a `.code-workspace` file with the name you want

Example:

```text
C:\Users\Administrator\Documents\cms2docs\cms-review.code-workspace
```

## 11. Recommended Habits For This Repo

- keep the main repo root on `main`
- name worktree directories after the review branch, e.g. `review-JE-1000F-JP` or `review-JE-1000F-US` (the review branch is `review/<MODEL>-<REGION>`)
- remove finished worktrees promptly after merge or close
- use `git worktree list -v` before creating a new one
- avoid forcing removal until you have checked whether the worktree contains local review edits or generated artifacts you still need
