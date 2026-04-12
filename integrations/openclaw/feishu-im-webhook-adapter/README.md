# Feishu IM Webhook Adapter

This package is the repo-external ingress layer for Feishu IM messages.

It does not build documents itself.
It receives Feishu callback events, normalizes text messages, calls the repo's existing
`build.py` control-surface commands, and replies back into the same Feishu thread.

Current command path:

```text
Feishu IM webhook
  -> feishu-im-webhook-adapter
  -> build.py queue-resolve-action
  -> build.py queue-query | build.py queue-execute
  -> Feishu reply
```

Current scope:

- `query_status`
- `start_review`
- `build_draft_package`
- `publish` with explicit confirmation

Current limitations:

- expects the callback security mode and runtime env to stay explicit
- uses the repo-local `build.py` CLI and the existing OpenClaw/GitHub dispatch path

## Environment

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `AUTO_MANUAL_REPO_ROOT`
- `AUTO_MANUAL_CONTROL_CONFIG`

Optional:

- `FEISHU_IM_VERIFICATION_TOKEN` or `FEISHU_VERIFICATION_TOKEN`
- `FEISHU_IM_ENCRYPT_KEY` or `FEISHU_ENCRYPT_KEY`
- `FEISHU_IM_WEBHOOK_HOST`
- `FEISHU_IM_WEBHOOK_PORT`
- `FEISHU_IM_WEBHOOK_PATH`
- `FEISHU_IM_HEALTH_PATH`
- `FEISHU_IM_REQUIRE_MENTION`
- `FEISHU_IM_PUBLISH_CONFIRM_TTL_SECONDS`
- `FEISHU_IM_STATE_FILE`
- `FEISHU_IM_ENCRYPT_KEY` or `FEISHU_ENCRYPT_KEY` when the Feishu app enables encrypted callbacks

## Run

```bash
node server.mjs
```

## ECS systemd

For a long-lived ECS deployment, use the service wrappers and unit examples in
[`deploy/systemd/`](deploy/systemd):

- [`deploy/systemd/README.md`](deploy/systemd/README.md)
- [`../../../../scripts/run_feishu_im_webhook_adapter_service.sh`](../../../../scripts/run_feishu_im_webhook_adapter_service.sh)
- [`../../../../scripts/run_feishu_im_cloudflared_service.sh`](../../../../scripts/run_feishu_im_cloudflared_service.sh)

Recommended production split:

- run the adapter under `systemd`
- run a named `cloudflared` tunnel under `systemd`
- point the Feishu callback URL at the named tunnel hostname

`trycloudflare.com` is acceptable for smoke tests, but not for a stable
callback URL after restarts.

## Test

```bash
npm test
```
