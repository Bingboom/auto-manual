# Integrations Directory

`integrations/` owns external runtime adapters, currently focused on OpenClaw and Feishu IM integration.

## Map

- `openclaw/`: BlockClaw/OpenClaw control layer, Feishu adapter, gateway patch scripts, and package docs.
- `openclaw/auto-manual-control-layer/`: local OpenClaw extension package.
- `openclaw/feishu-im-webhook-adapter/`: Feishu IM webhook ingress package.
- `openclaw/scripts/`: gateway patch and persona wiring guard scripts.

## Local Rules

- Keep OpenClaw/BlockClaw code here, not under `tools/`, so the JS control layer stays separate from the Python execution plane.
- Do not edit `agent/BOOTSTRAP.md`, `agent/IDENTITY.md`, `agent/SOUL.md`, or `agent/USER.md` during integration work unless the task is explicitly about persona content.
- Keep generated `node_modules/` and runtime directories out of reasoning and commits.

## Validation

- Python lint for integration-adjacent code: `python3 -m ruff check integrations`
- OpenClaw control layer tests: `npm test --prefix integrations/openclaw/auto-manual-control-layer`
- Feishu adapter tests: `npm test --prefix integrations/openclaw/feishu-im-webhook-adapter`
- External integration contracts: `python3 -m unittest tests.test_external_integration_contracts tests.test_openclaw_workflow_run_metadata`
