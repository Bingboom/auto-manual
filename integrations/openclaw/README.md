# OpenClaw Integrations

This directory owns the repository-facing OpenClaw control-layer assets.

Canonical docs:

- [`../../BOOTSTRAP.md`](../../BOOTSTRAP.md)
- [`../../code-as-doc/architecture/OpenClaw_Control_Layer_Plan.md`](../../code-as-doc/architecture/OpenClaw_Control_Layer_Plan.md)
- [`../../code-as-doc/build_doc_guide.md`](../../code-as-doc/build_doc_guide.md)

Current package:

- [`auto-manual-control-layer/`](auto-manual-control-layer)
  - local OpenClaw plugin package for dispatching the repo's `main`-owned GitHub workers
  - registers `/start-review`, `/build-draft`, `/publish`, and `/manual-status`
- [`feishu-im-webhook-adapter/`](feishu-im-webhook-adapter)
  - standalone Feishu IM webhook ingress for the same control layer
  - receives Feishu text messages, normalizes them, calls `build.py queue-resolve-action|queue-query|queue-execute`, and replies back into the same thread

Keep OpenClaw code here, not under [`tools/`](../../tools), so the control layer stays separate from the Python execution plane.
