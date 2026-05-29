# Claude Code Entrypoint

This file is the Claude Code entrypoint for this repo. The repo's operating rules live in [`AGENTS.md`](AGENTS.md), which every AI agent (Claude, Codex, future agents) shares. Read it first.

@AGENTS.md

## When opening a new Claude window

A new window has no memory of the previous one. Before touching the working tree:

1. Confirm clean state and create a fresh branch with the wrapper:

   ```powershell
   git fetch origin
   git status
   powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 <type>/<area>-<topic>
   ```

   `<type>` is one of `feat`, `fix`, `refactor`, `docs`, `chore`, `review`, `spike`, `release` — never the agent name. See [`AGENTS.md`](AGENTS.md) §8.1 and [`code-as-doc/dev/git_branching_guide.md`](code-as-doc/dev/git_branching_guide.md) §2.

2. If another window may be working in this checkout in parallel, open a `git worktree` per [`code-as-doc/dev/git_worktree_guide.md`](code-as-doc/dev/git_worktree_guide.md) instead of sharing the checkout.

3. Follow the rest of [`AGENTS.md`](AGENTS.md) §8 for concurrency safety, commit discipline, local validation, and the PR flow.

## Notes specific to Claude Code

- Operator: 唐夏冰 (call them 夏冰). See [`USER.md`](USER.md) for tone and timezone context.
- For chat-facing identity (BlockClaw role, voice rules), see [`BOOTSTRAP.md`](BOOTSTRAP.md), [`IDENTITY.md`](IDENTITY.md), [`SOUL.md`](SOUL.md). Those describe the chat persona running on top of OpenClaw; **they are not** the repo coding rules. Do not edit them while doing engineering tasks.
- This file should stay thin. New rules go into [`AGENTS.md`](AGENTS.md) so Codex and any future agent inherit them automatically.
