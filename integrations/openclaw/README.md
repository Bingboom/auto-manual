# OpenClaw Integrations

This directory owns the repository-facing OpenClaw control-layer assets.
The repo-specific operator identity for these assets is **BlockClaw**.
OpenClaw is the runtime and gateway; BlockClaw is the Auto-Manual document-build operator that understands content blocks, queue rows, review bundles, and publish artifacts.

Canonical docs:

- [`IDENTITY.md`](IDENTITY.md)
- [`../../BOOTSTRAP.md`](../../BOOTSTRAP.md)
- [`../../code-as-doc/architecture/OpenClaw_Control_Layer_Plan.md`](../../code-as-doc/architecture/OpenClaw_Control_Layer_Plan.md)
- [`../../code-as-doc/build_doc_guide.md`](../../code-as-doc/build_doc_guide.md)

Current package:

- [`auto-manual-control-layer/`](auto-manual-control-layer)
  - local OpenClaw plugin package that exposes the BlockClaw operator surface for dispatching the repo's `main`-owned GitHub workers
  - registers `/start-review`, `/build-draft`, `/publish`, and `/manual-status`
- [`feishu-im-webhook-adapter/`](feishu-im-webhook-adapter)
  - standalone Feishu IM webhook ingress for the same BlockClaw control layer
  - receives Feishu text messages, normalizes them, calls `build.py queue-resolve-action|queue-query|queue-execute`, and replies back into the same thread
- [`scripts/patch_openclaw_feishu_received_reaction.mjs`](scripts/patch_openclaw_feishu_received_reaction.mjs)
  - local OpenClaw gateway patcher for adding the native Feishu `Get` reaction immediately after `im.message.receive_v1`
  - runs before gateway startup from LaunchAgent when the machine uses the upstream OpenClaw gateway instead of the repo adapter

Keep OpenClaw / BlockClaw code here, not under [`tools/`](../../tools), so the control layer stays separate from the Python execution plane.

## Native OpenClaw gateway reaction patch

The repo adapter can add Feishu reactions through its own message handler, but
the always-on desktop flow may receive messages through the installed OpenClaw
gateway instead. In that path the acknowledgement must happen at the Feishu IM
event layer, before any agent reasoning, queue lookup, or document build work.

Use the patcher when a local OpenClaw gateway should acknowledge every accepted
incoming Feishu IM with the native `Get` emoji:

```bash
node integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs
```

The script scans the installed OpenClaw `dist/` bundle, injects a best-effort
`messageReaction.create` call into the `im.message.receive_v1` handler, and
leaves the normal text reply path untouched. It is idempotent and writes a
`.before-feishu-received-reaction` backup before the first patch.

For a stable local service, run the patcher before `openclaw gateway` starts in
the user LaunchAgent. That makes package overwrites self-heal on the next
service start while keeping the actual patch source in this repo. The default
install root is `/opt/homebrew/opt/manual-node-v24.14.1/lib/node_modules/openclaw`;
override it with `OPENCLAW_INSTALL_ROOT` if OpenClaw is installed elsewhere.
