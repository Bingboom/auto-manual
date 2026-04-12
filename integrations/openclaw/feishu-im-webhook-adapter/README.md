# Feishu IM Webhook Adapter

This package is the repo-external ingress layer for Feishu IM messages.

It does not build documents itself.
It receives Feishu callback events, normalizes text messages, calls the repo's existing
`build.py` control-surface commands, and replies back into the same Feishu thread.

Current command path:

```text
Feishu IM webhook
  -> feishu-im-webhook-adapter
  -> build.py dingtalk-control-config | queue-resolve-action
  -> build.py queue-query | build.py queue-execute
  -> Feishu reply
```

Current scope:

- `dingtalk-control-config` read/update from chat text
- `query_status`
- `start_review`
- `build_draft_package`
- `publish` with explicit confirmation

Supported DingTalk control phrases:

- `查看钉钉配置`
- `dingtalk-config`
- `绑定钉钉 <operator_union_id> <https://alidocs.dingtalk.com/i/nodes/...>`
- `dingtalk-bind <operator_union_id> <https://alidocs.dingtalk.com/i/nodes/...>`

Current limitations:

- expects plain event callbacks plus verification token validation
- does not yet implement Feishu encrypted callback payload decryption
- uses the repo-local `build.py` CLI and the existing OpenClaw/GitHub dispatch path

## Environment

- `FEISHU_IM_VERIFICATION_TOKEN` or `FEISHU_VERIFICATION_TOKEN`
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `AUTO_MANUAL_REPO_ROOT`
- `AUTO_MANUAL_CONTROL_CONFIG`

Optional:

- `FEISHU_IM_WEBHOOK_HOST`
- `FEISHU_IM_WEBHOOK_PORT`
- `FEISHU_IM_WEBHOOK_PATH`
- `FEISHU_IM_HEALTH_PATH`
- `FEISHU_IM_REQUIRE_MENTION`
- `FEISHU_IM_PUBLISH_CONFIRM_TTL_SECONDS`
- `FEISHU_IM_STATE_FILE`

You can copy [`.env.example`](./.env.example) as the local env template.

## Run

```bash
../../scripts/run_feishu_im_webhook_adapter.sh
```

Windows:

```powershell
..\..\..\scripts\run_feishu_im_webhook_adapter.ps1
```

## Deploy

1. Start the adapter on a local machine or a small always-on host, then expose it to Feishu over HTTPS.
2. Keep the health check at `GET /healthz` and the callback URL at `POST /feishu/events` unless you also override `FEISHU_IM_HEALTH_PATH` or `FEISHU_IM_WEBHOOK_PATH`.
3. In the Feishu Open Platform app:
   - use the same app whose `FEISHU_APP_ID` and `FEISHU_APP_SECRET` the adapter is using
   - set the event subscription request URL to `https://<your-host>/feishu/events`
   - set the verification token to the same value as `FEISHU_IM_VERIFICATION_TOKEN`
   - keep callbacks in plain mode for now; this adapter rejects encrypted payloads
   - subscribe to `im.message.receive_v1`
   - publish the app change, then add the app bot into the target chat
4. The same app still needs the existing repo Feishu table access and message reply capability, because the adapter replies through `im/v1/messages/:message_id/reply`.

For the smallest macOS deployment shape, use the templates under [`deploy/`](./deploy/):

- [`deploy/env.sh.example`](./deploy/env.sh.example)
- [`deploy/cloudflared/config.example.yml`](./deploy/cloudflared/config.example.yml)
- [`deploy/launchd/com.auto-manual.feishu-im-webhook-adapter.plist.example`](./deploy/launchd/com.auto-manual.feishu-im-webhook-adapter.plist.example)
- [`deploy/launchd/com.auto-manual.feishu-im-cloudflared.plist.example`](./deploy/launchd/com.auto-manual.feishu-im-cloudflared.plist.example)
- [`deploy/README.md`](./deploy/README.md)

## GitHub Worker

For the long-lived `dingtalk_openapi` upload path, the remote GitHub queue workers now read these repository secrets directly:

- `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=dingtalk_openapi`
- `DINGTALK_CLIENT_ID`
- `DINGTALK_CLIENT_SECRET`
- `DINGTALK_CORP_ID`
- `FEISHU_PHASE2_DINGTALK_CONTROL_TABLE_ID`
- `FEISHU_PHASE2_DINGTALK_CONTROL_VIEW_ID`
- optional `FEISHU_PHASE2_DINGTALK_CONTROL_RECORD_ID`

The adapter itself does not need those DingTalk app secrets. It only writes `operator_union_id` plus `default_target_node_url` into the Feishu control row. The GitHub worker reads that control row and combines it with the `DINGTALK_*` secrets during upload.

## Credential Mapping

- `DINGTALK_CLIENT_ID`: the DingTalk app `AppKey` or `Client ID`
- `DINGTALK_CLIENT_SECRET`: the matching DingTalk app secret
- `DINGTALK_CORP_ID`: the tenant `CorpId`

If your DingTalk console labels the first field as `AppKey` instead of `Client ID`, map `AppKey -> DINGTALK_CLIENT_ID`.

## Direct Run

```bash
node server.mjs
```

## Test

```bash
npm test
```
