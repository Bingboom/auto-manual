# Feishu IM Adapter Minimal Deploy

This directory contains the smallest deployment shape that makes the Feishu IM webhook adapter reachable from Feishu:

- local adapter process
- local `cloudflared` tunnel
- one stable HTTPS callback hostname

Recommended target host for this minimal setup:

- macOS machine that can stay online
- Homebrew available
- repo already checked out locally

## Files

- [`env.sh.example`](./env.sh.example): local adapter env file template
- [`cloudflared/config.example.yml`](./cloudflared/config.example.yml): named tunnel config template
- [`launchd/com.auto-manual.feishu-im-webhook-adapter.plist.example`](./launchd/com.auto-manual.feishu-im-webhook-adapter.plist.example): adapter launch agent template
- [`launchd/com.auto-manual.feishu-im-cloudflared.plist.example`](./launchd/com.auto-manual.feishu-im-cloudflared.plist.example): cloudflared launch agent template

## Minimal Path

1. Install local runtime:
   - `brew install cloudflared`
   - `cd integrations/openclaw/feishu-im-webhook-adapter && npm install`
2. Create the adapter env file:
   - copy [`env.sh.example`](./env.sh.example) to `.tmp/feishu-im-webhook-adapter/env.sh`
   - fill `FEISHU_IM_VERIFICATION_TOKEN`, `FEISHU_APP_ID`, `FEISHU_APP_SECRET`
3. Create a named tunnel:
   - `cloudflared tunnel login`
   - `cloudflared tunnel create auto-manual-feishu-im`
   - `cloudflared tunnel route dns auto-manual-feishu-im feishu-im.example.com`
4. Create the local tunnel config:
   - copy [`cloudflared/config.example.yml`](./cloudflared/config.example.yml) to `cloudflared/config.yml`
   - replace the tunnel id, credentials file path, and hostname
5. Run locally once:
   - `FEISHU_IM_ENV_FILE="$PWD/.tmp/feishu-im-webhook-adapter/env.sh" ./scripts/run_feishu_im_webhook_adapter.sh`
   - `cloudflared tunnel --config integrations/openclaw/feishu-im-webhook-adapter/deploy/cloudflared/config.yml run`
6. After both processes stay healthy, set the Feishu event callback URL to:
   - `https://feishu-im.example.com/feishu/events`
7. Then convert both processes into launch agents with the plist templates in [`launchd/`](./launchd)

## Feishu App Settings

- callback mode: plain
- event subscription: `im.message.receive_v1`
- verification token: must match `FEISHU_IM_VERIFICATION_TOKEN`
- bot/app must be published after changing event subscription

## GitHub Worker Secrets

For the remote `dingtalk_openapi` worker path, set repository secrets:

- `AUTO_MANUAL_ARTIFACT_SINK_PROVIDER=dingtalk_openapi`
- `DINGTALK_CLIENT_ID`
- `DINGTALK_CLIENT_SECRET`
- `DINGTALK_CORP_ID`
- `FEISHU_PHASE2_DINGTALK_CONTROL_TABLE_ID`
- `FEISHU_PHASE2_DINGTALK_CONTROL_VIEW_ID`
- optional `FEISHU_PHASE2_DINGTALK_CONTROL_RECORD_ID`

The adapter host does not need those DingTalk app secrets.
