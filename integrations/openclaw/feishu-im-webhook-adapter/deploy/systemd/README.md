# ECS systemd deployment

This directory contains the minimal deployment assets for running the Feishu IM
webhook adapter on a long-lived Linux host such as Alibaba Cloud ECS.

What this solves:

- boot-time start for the adapter
- automatic restart when the adapter process exits
- optional boot-time start for `cloudflared`

What this does not solve by itself:

- a stable public callback URL if you still use `trycloudflare.com`

`trycloudflare.com` is fine for short-lived smoke tests, but it is not stable
across restarts. For a stable Feishu callback URL, use one of these:

- a named Cloudflare Tunnel with a real hostname
- your own HTTPS reverse proxy in front of the adapter

## 1. Repo assumptions

The examples below assume the repo is deployed at:

- `/opt/auto-manual`

and the adapter env file lives at:

- `/opt/auto-manual/.tmp/feishu-im-webhook-adapter/env.sh`

The service wrappers source that shell env file directly, so the file may
contain `export ...` lines and shell snippets such as NVM bootstrap.

## 2. Required env in `env.sh`

Minimum adapter runtime:

```bash
export FEISHU_IM_VERIFICATION_TOKEN=your_verification_token
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export AUTO_MANUAL_CONTROL_CONFIG=configs/config.us.yaml
export FEISHU_IM_WEBHOOK_HOST=127.0.0.1
export FEISHU_IM_WEBHOOK_PORT=9097
export FEISHU_IM_WEBHOOK_PATH=/feishu/events
export FEISHU_IM_HEALTH_PATH=/healthz
export FEISHU_IM_REQUIRE_MENTION=true
export FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true
export AUTO_MANUAL_PYTHON=/opt/auto-manual/.venv/bin/python
export FEISHU_PHASE2_IDENTITY=bot
```

Only enable `FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true` after the Feishu app has
message reaction permission. With reactions enabled, the adapter sends the
default `Get` reaction as soon as it accepts an incoming message.

If the adapter must resolve or execute queue rows, also set the current Feishu
Phase 2 bindings in the same file:

```bash
export FEISHU_PHASE2_BASE_TOKEN=app_xxx
export FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID=tbl_xxx
export FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID=vew_xxx
```

If `node` is installed through NVM, keep these lines in the same env file so
the wrapper can restore `node` under systemd:

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
```

## 3. Named Cloudflare Tunnel

For a stable public callback URL, prefer a named tunnel. Add one of these to
`env.sh`:

```bash
export CLOUDFLARED_TUNNEL_TOKEN=xxxxxxxxxxxxxxxx
```

or:

```bash
export CLOUDFLARED_TUNNEL_CONFIG=/etc/cloudflared/config.yml
```

If you use a config file, start from
[`cloudflared.named.example.yml`](./cloudflared.named.example.yml).

### 3.1 Deferred server TODO for a stable public URL

If the adapter is already working through `trycloudflare.com`, but the stable
hostname rollout is being deferred, keep this exact ECS follow-up checklist:

1. provision or delegate one real domain to Cloudflare DNS
2. choose one stable hostname for the adapter, for example
   `feishu-im.example.com`
3. run `cloudflared tunnel create auto-manual-feishu-im`
4. run `cloudflared tunnel route dns auto-manual-feishu-im feishu-im.example.com`
5. write `/etc/cloudflared/config.yml` with the named tunnel UUID, the
   matching credentials file under `/root/.cloudflared/`, and
   `service: http://127.0.0.1:9097`
6. add `export CLOUDFLARED_TUNNEL_CONFIG=/etc/cloudflared/config.yml` to
   `/opt/auto-manual/.tmp/feishu-im-webhook-adapter/env.sh`
7. enable `auto-manual-feishu-im-cloudflared.service` under `systemd`
8. update the Feishu event callback URL from the temporary
   `trycloudflare.com` host to
   `https://feishu-im.example.com/feishu/events`
9. verify `https://feishu-im.example.com/healthz` before treating the old
   `trycloudflare.com` URL as retired

Do not treat this as optional cleanup. The adapter process can be stable under
`systemd` while the public callback URL is still unstable if the ingress layer
remains on `trycloudflare.com`.

## 4. Install the systemd units

Copy the example units into `/etc/systemd/system/`:

```bash
sudo cp /opt/auto-manual/integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/auto-manual-feishu-im-webhook-adapter.service.example \
  /etc/systemd/system/auto-manual-feishu-im-webhook-adapter.service

sudo cp /opt/auto-manual/integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/auto-manual-feishu-im-cloudflared.service.example \
  /etc/systemd/system/auto-manual-feishu-im-cloudflared.service
```

Enable the adapter:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now auto-manual-feishu-im-webhook-adapter
```

Enable the named tunnel only after `CLOUDFLARED_TUNNEL_TOKEN` or
`CLOUDFLARED_TUNNEL_CONFIG` is configured:

```bash
sudo systemctl enable --now auto-manual-feishu-im-cloudflared
```

## 5. Verify

Adapter:

```bash
systemctl status auto-manual-feishu-im-webhook-adapter --no-pager
journalctl -u auto-manual-feishu-im-webhook-adapter -n 100 --no-pager
curl http://127.0.0.1:9097/healthz
```

Cloudflared:

```bash
systemctl status auto-manual-feishu-im-cloudflared --no-pager
journalctl -u auto-manual-feishu-im-cloudflared -n 100 --no-pager
```

## 6. Restart after repo updates

When the repo or `env.sh` changes:

```bash
sudo systemctl restart auto-manual-feishu-im-webhook-adapter
sudo systemctl restart auto-manual-feishu-im-cloudflared
```

## 7. Current stable-path recommendation

Use this split in production:

- adapter under `systemd`
- named `cloudflared` tunnel under `systemd`
- Feishu callback URL pointed at the named tunnel hostname

Do not treat `trycloudflare.com` as a stable callback endpoint for production.
