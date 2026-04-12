# OpenClaw Bootstrap

Updated: 2026-04-12

Use this file only as the short entrypoint for the repo's current OpenClaw surface.
It is not the detailed architecture plan and it is not the full workflow guide.

## 1. Current Role

This repo can act as a natural-language operator surface for the manual workflow, but the execution plane stays unchanged:

- Feishu phase2 tables remain the source of truth
- `build.py queue-query`, `queue-resolve-action`, and `queue-execute` are the repo-owned control surface
- GitHub Actions on `main` remain the remote execution plane
- `Document link` remains the canonical returned artifact link field

## 2. Canonical Docs

Read these docs for the current implementation:

- [`integrations/openclaw/README.md`](integrations/openclaw/README.md)
- [`code-as-doc/architecture/OpenClaw_Control_Layer_Plan.md`](code-as-doc/architecture/OpenClaw_Control_Layer_Plan.md)
- [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)

## 3. Minimal Commands

Query one target row from natural language:

```powershell
python build.py queue-query --config config.us.yaml --query-text "<user request>" --json
```

Resolve one natural-language ask into a bounded action contract:

```powershell
python build.py queue-resolve-action --config config.us.yaml --query-text "<user request>" --json
```

Dispatch one natural-language execution ask:

```powershell
python build.py queue-execute --config config.us.yaml --query-text "<user request>"
```

Run the standalone Feishu IM ingress adapter:

```powershell
node integrations/openclaw/feishu-im-webhook-adapter/server.mjs
```

## 4. Maintenance Rule

- Keep this file short and current.
- If detailed behavior changes, update the owning docs above instead of expanding this file back into a long plan.
