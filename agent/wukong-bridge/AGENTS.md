# Wukong Bridge Agent Guide

This directory is the Git source of truth for the DingTalk Wukong MCP bridge.

## Scope

- `server.py`: stdio MCP server and tool contracts.
- `intake_contract.py`: pure, testable staging and intake gates.
- `intake_commit_driver.py`: approval-gated formal Base writes and readback.
- `gate_*_driver.py`: long-running IDML diagnostics/rebind jobs.
- `test_intake_contract.py`: targeted contract regression tests.

Runtime state, credentials, exports, jobs, caches, and virtual environments do
not belong in this directory. Keep them in the external state/env locations
documented in `README.md`.

## Safety

- Intake staging may write only the staging table. Formal source-table writes
  remain behind both the Base checkbox and explicit conversational approval.
- Read live sibling and target rows before claiming completeness or absence.
- Keep `LARK_CLI_PROFILE=prod` and `LARK_CLI_IDENTITY=bot` explicit in deployed
  configuration; never commit authentication material.
- Do not add a target-specific repair script to the supported server contract.
  Generalize a validation rule and cover it with a unit test instead.

## Validation

Run from this directory:

```bash
python3 -m ruff check .
python3 -m unittest -v test_intake_contract.py
python3 -m py_compile *.py
```
