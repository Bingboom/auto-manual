# OpenClaw Integrations

This directory owns the repository-facing OpenClaw control-layer assets.

Current package:

- [`auto-manual-control-layer/`](auto-manual-control-layer)
  - local OpenClaw plugin package for dispatching the repo's `main`-owned GitHub workers
  - registers `/start-review`, `/build-draft`, `/publish`, and `/manual-status`

Keep OpenClaw code here, not under [`tools/`](../../tools), so the control layer stays separate from the Python execution plane.
