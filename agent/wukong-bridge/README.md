# Hello-Docs Wukong Bridge

This directory is the version-controlled source of truth for the stdio MCP
bridge used by DingTalk Wukong to operate the auto-manual workspace.

The bridge exposes bounded workspace capabilities such as TM lookup, build
queue operations, IDML gate jobs, and approval-gated source intake. It does not
store Feishu credentials.

## Repository and runtime boundary

Committed here:

- MCP tool definitions and handlers;
- intake contracts and commit driver;
- IDML job drivers;
- regression tests and operator documentation.

Never commit here:

- `.env`, tokens, cookies, passwords, app secrets, or CLI auth stores;
- `.venv`, `__pycache__`, logs, jobs, exports, downloaded documents, or build
  artifacts;
- one-off live-record repair scripts with hard-coded record IDs.

Runtime state defaults to `~/.local/state/hello-docs-bridge`. Override it with
`HELLO_DOCS_BRIDGE_STATE_DIR`. Optional environment files are external and are
selected with `HELLO_DOCS_BRIDGE_ENV_FILES`; the bridge never copies them into
the repository.

Base tokens and table IDs in the code are resource coordinates, not
authentication credentials. Authentication remains in the selected `lark-cli`
profile.

## MCP registration

Use the repository Python environment and the checked-in server path. Replace
`/absolute/path/to/auto-manual2` with this repository's real absolute path on
the current computer. Do not rely on `~` expansion inside MCP JSON:

```json
{
  "name": "hello-docs-bridge",
  "type": "stdio",
  "command": "/absolute/path/to/auto-manual2/.venv/bin/python3",
  "args": [
    "/absolute/path/to/auto-manual2/agent/wukong-bridge/server.py"
  ],
  "env": {
    "AUTO_MANUAL_REPO_ROOT": "/absolute/path/to/auto-manual2",
    "AUTO_MANUAL_CONTROL_CONFIG": "/absolute/path/to/auto-manual2/configs/config.us.yaml",
    "LARK_CLI_PROFILE": "prod",
    "LARK_CLI_IDENTITY": "bot"
  }
}
```

`AUTO_MANUAL_REPO_ROOT` is the preferred workspace variable;
`HELLO_DOCS_REPO_ROOT` remains a compatibility fallback for older MCP
registrations. IDML gate diagnostics use the same checkout by default. Set
`HELLO_DOCS_MIRROR_ROOT` only when those jobs intentionally run against a
separate Hello-Docs mirror checkout. A non-secret variable template is in
[`.env.example`](.env.example); keep the real environment file outside Git.

No bridge-specific Python dependency installation is required: the server uses
the standard library and delegates workspace work to the repository runtime and
`lark-cli`.

After changing the MCP path or updating the checked-in server, restart/reconnect
the Wukong MCP process. Call `bridge_info`; the current contract must report:

```text
server_version = 0.8.0
intake_contract_version = kr-structured-source-first-v2
bridge_source_dir = .../auto-manual2/agent/wukong-bridge
```

## KR intake flow

For a new Korean target, Wukong must use an explicit sibling structure. For
`JE-2000E_KR`, use `JE-2000E_US` unless the operator chooses another baseline.

1. Call `intake_status(document_key, sibling_document_key)` and read both the
   staging state and the two formal source-table counts.
2. Extract candidate facts from operator-provided evidence. Put the original
   evidence in `规格书原值`; write canonical English in `手册值` and `行标签`;
   set `Source_lang=en`. Korean belongs only in the optional `*_ko` fields.
3. Map every candidate to the sibling identity
   `Page + Row_key + Slot_key + Section + Line_order`. Do not invent a key,
   collapse input/output rows, or route storage rows to `specifications`.
4. Call `intake_stage` with both `document_key` and
   `sibling_document_key`. The write is atomic: any source/semantic/structure
   violation means `staged=0`. A valid partial batch can be staged, but the
   response lists `coverage_missing_rows` and must not be presented as a
   complete intake.
   If an older pending batch is structurally wrong, first show its record IDs
   to the operator. Only after the operator explicitly approves “作废旧暂存” may
   Wukong call `intake_discard`; it writes an auditable `已作废` marker and does
   not delete records or touch either formal source table.
5. The operator reviews values and selects `确认` in Base. Formal intake remains
   blocked until specs and placeholders together cover the sibling structure.
6. Only after the operator explicitly says “入库” may Wukong call
   `intake_commit(confirm_ingest=true, approved_by=..., sibling_document_key=...)`.
   The driver performs a second complete preflight, writes formal tables, reads
   every row back, then updates the staging result.

Important JE-2000E rules enforced by the general contract:

- storage rows use `Page=storage` and the fixed order 1 month = 1,
  3 months = 2, 1 year/12 months = 3;
- the 30 W and 140 W USB-C rows retain their sibling Slot_key/Line_order;
- expansion-port input and output are separate Section rows;
- English source values use manual unit spacing (`2048 Wh`, `19.1 kg`,
  `25 °C`) and the DC symbol (`5 V⎓3 A`), not an equals sign.

## Validation

Run from this directory:

```bash
python3 -m ruff check .
python3 -m unittest -v test_intake_contract.py
python3 -m py_compile *.py
```
