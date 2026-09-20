# macOS product VOC receiver

This runbook manages the existing `integrations.product_voc.server` receiver on
the designated Mac. It is an explicit operator action: the repository does not
install a daemon, start it at login, keep the Mac awake, configure OpenClaw or
create a public tunnel.

## Prerequisites

Use the macOS account that owns the existing `lark-cli` credentials. The verified
HT-Docs bot profile on this host is `cli_aaa0db0d4b39dcca`. Before starting the
receiver, verify that identity and the fixed destination without printing or
copying credentials:

```bash
lark-cli --profile cli_aaa0db0d4b39dcca auth status --json --verify
lark-cli --profile cli_aaa0db0d4b39dcca base +field-list \
  --as bot --base-token Id29bqWMiaFdNjsuyrAcfrkLnZb \
  --table-id tblmN7OHIB0HsC23 --limit 200 --format json
```

The receiver itself repeats the field preflight before opening the socket. It
uses the existing profile through `lark-cli --as bot`; it does not store the
credential in its runtime directory. Use the repository `.venv` prepared from
`requirements.lock`; the service does not install dependencies at startup.

## Run and inspect

For an attended integration test, run in the foreground:

```bash
.venv/bin/python scripts/voc_mac_receiver.py run \
  --profile cli_aaa0db0d4b39dcca \
  --base Id29bqWMiaFdNjsuyrAcfrkLnZb --table tblmN7OHIB0HsC23 \
  --origin https://ht-doc.readthedocs.io
```

For a manually managed background process, replace `run` with `start`. The
wrapper waits for `http://127.0.0.1:9198/healthz` before reporting success:

```bash
.venv/bin/python scripts/voc_mac_receiver.py start \
  --profile cli_aaa0db0d4b39dcca \
  --base Id29bqWMiaFdNjsuyrAcfrkLnZb --table tblmN7OHIB0HsC23 \
  --origin https://ht-doc.readthedocs.io
.venv/bin/python scripts/voc_mac_receiver.py status
.venv/bin/python scripts/voc_mac_receiver.py stop
```

The default private runtime directory is
`~/Library/Application Support/auto-manual/product-voc` with mode `0700`.
`receipts.sqlite`, `receiver.pid`, and `receiver.log` remain there; files created
by the wrapper are private. Use the same `--runtime-dir /absolute/path` on every
command when overriding it. Back up the receipt database before moving hosts.

The listener is fixed to `127.0.0.1`. `--preview` additionally serves the marked
local test form. `--cloudflare-tunnel` only changes which peer address is trusted
for rate limiting; it does not install, configure or start Cloudflare Tunnel.
Add either switch only for the corresponding supervised integration test.

## Operational boundaries

`/healthz` proves that the local process answers; it does not prove a current
Feishu write or public reachability. A real end-to-end test requires an explicitly
marked `TEST` submission and readback of that record under the product VOC
acceptance procedure. The wrapper never submits a record itself.

Stopping the receiver disables local intake but preserves the log, receipts and
Feishu rows. There is no automatic restart after logout, reboot or sleep. Public
service needs a separately approved, stable HTTPS ingress targeting only this
loopback port. Do not expose the OpenClaw gateway, commit a tunnel URL, or enable
the website endpoint until external and duplicate-submission acceptance passes.
