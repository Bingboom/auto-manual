# Feishu IM Adapter

This package owns both Feishu IM ingress modes for the repo control layer:

- webhook mode for a public HTTPS callback
- local long-connection mode for a no-server local machine

It does not build documents itself.
It receives Feishu events, normalizes text messages, calls the repo's existing
`build.py` control-surface commands, and replies back into the same Feishu thread.

Current command path:

```text
Feishu IM event
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
- `FEISHU_IM_LARK_CLI_BIN` for local long-connection mode
- `FEISHU_IM_EVENT_IDENTITY` for local long-connection mode; defaults to `bot`
- `FEISHU_IM_LARK_CLI_HOME` for local long-connection mode when the new app must use an isolated `lark-cli` home and must not reuse the default `~/.lark-cli`

## Run

Webhook mode:

```bash
node server.mjs
```

Local no-server mode:

```bash
node local-listener.mjs --control-config ../../../config.us.yaml
python ../../../build.py listen-message-control --config config.us.yaml
```

Local mode uses `lark-cli event +subscribe` for `im.message.receive_v1`, so it
does not need any public callback URL or tunnel. The Feishu app still needs that
event enabled and published in the Open Platform console.

When the machine must keep an older Feishu app under the default `~/.lark-cli`,
point the new app listener at an isolated `lark-cli` home:

```bash
export FEISHU_IM_LARK_CLI_HOME="$HOME/.feishu-im-newapp"
mkdir -p "$FEISHU_IM_LARK_CLI_HOME"
HOME="$FEISHU_IM_LARK_CLI_HOME" printf '%s' "$FEISHU_IM_APP_SECRET" | lark-cli config init --app-id "$FEISHU_IM_APP_ID" --app-secret-stdin --brand feishu
python ../../../build.py listen-message-control --config config.us.yaml
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
