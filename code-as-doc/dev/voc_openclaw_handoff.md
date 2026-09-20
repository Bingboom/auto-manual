# VOC to local OpenClaw handoff

This optional post-intake command lets an operator send one already verified
product suggestion to the local HT-Docs OpenClaw `main` agent. It is deliberately
separate from HTTP intake: the receiver never invokes a model, and this command
is not a daemon, webhook, scheduler or public gateway route.

## Contract

The operator must supply both the website submission UUID and exact Feishu
`record_id`. The command opens the intake SQLite database read-only and requires
the receipt to be `verified=1` with that record ID. It then reads only that row
through the explicitly selected HT-Docs bot profile and recomputes the intake
payload digest. Any missing receipt, record mismatch or changed source text
stops before OpenClaw runs.

The OpenClaw invocation uses its installed CLI contract:

```text
openclaw agent --agent main --session-key agent:main:voc:<UUID> --message <bounded prompt> --json
```

The utility calls the installed Node entry file directly because `openclaw` need
not be on `PATH`. `--agent main` is fixed, and the deterministic scoped session key keeps
VOC work outside existing Feishu/DingTalk conversations. The command never adds
`--deliver`, channel or reply options. It connects to the already loopback-bound
gateway through the CLI; it does not start, reconfigure or expose the gateway.

Visitor text is serialized under `UNTRUSTED_VOC_DATA`. The prompt requires a
review memo, labels the text as untrusted data, and forbids tool use, messages,
file edits and Feishu/source-table writes. The output remains a local candidate
for human review; it does not approve a product change or manual correction.
This prompt boundary is advisory: the installed `main` agent retains its configured
tool profile. The explicit operator invocation and local review are therefore the
control boundary; this utility does not claim hard tool sandboxing.

## Operator run

Use private, durable absolute paths outside Git. On this host the verified bot
profile is `cli_aaa0db0d4b39dcca`; re-check its identity before the first real
run. The explicit `--invoke` flag authorizes one local model call.

```bash
python -m integrations.product_voc.openclaw_handoff \
  --invoke \
  --state /absolute/private/runtime/voc.sqlite \
  --runtime-dir /absolute/private/runtime/voc-openclaw \
  --submission-id 00000000-0000-4000-8000-000000000000 \
  --record-id recEXACT \
  --base Id29bqWMiaFdNjsuyrAcfrkLnZb \
  --table tblmN7OHIB0HsC23 \
  --lark-profile cli_aaa0db0d4b39dcca \
  --openclaw-node /opt/homebrew/opt/node/bin/node \
  --openclaw-entry /Users/hello-tech-team/agent-runtimes/openclaw/lib/node_modules/openclaw/dist/index.js
```

One JSON analysis is written under `analysis/`, and its hash, source digest,
exact references, `main` agent choice and isolated session key are written under
`receipts/`. Files are mode `0600` and directories are mode `0700`; the receipt
does not repeat the suggestion text. A completed receipt with matching output is
returned without a second record read or model call, which bounds repeat cost.

If OpenClaw exits unsuccessfully, returns invalid JSON, or the process stops
after the prepared receipt is created, the receipt remains `failed` or
`prepared`. Later runs refuse to invoke the agent again. Inspect the recorded
session and local files to determine whether work occurred; do not delete the
receipt and blindly retry. A later retry/reconciliation command needs a separate
reviewed design because model execution has no transactional idempotency key.

This utility performs a Feishu record read and local file writes only. It has no
record-create/update command, no source-table path, no outgoing message delivery,
and no website or receiver integration.

## Verification

```bash
python3 -m unittest tests.test_product_voc_openclaw_handoff
python3 -m ruff check integrations/product_voc/openclaw_handoff.py \
  tests/test_product_voc_openclaw_handoff.py
python3 tools/check_doc_link_integrity.py
```
