# DingTalk IM Adapter

This package is the DingTalk counterpart of
[`../feishu-im-webhook-adapter/`](../feishu-im-webhook-adapter). It receives
DingTalk enterprise-robot messages over **Stream mode** (a long connection, so
no public callback URL is needed), normalizes the text, calls the repo's
existing `build.py` control-surface commands, and replies back into the same
DingTalk conversation.

It does not build documents itself. The queue resolve/execute/poll orchestration
(including batch dispatch and status follow-ups) is the same channel-neutral code
the Feishu adapter uses; only the ingress (DingTalk Stream) and egress (DingTalk
reply API) differ.

Current command path:

```text
DingTalk IM Stream event
  -> dingtalk-im-adapter (DWClient TOPIC_ROBOT)
  -> build.py queue-resolve-action
  -> build.py queue-query | build.py queue-execute
  -> DingTalk reply (sessionWebhook, or robot oToMessages/groupMessages)
```

## Relationship to the OpenClaw `ddingtalk` channel

OpenClaw can also connect DingTalk as a conversational channel via the
`@largezhou/ddingtalk` plugin (`channels.ddingtalk` in `openclaw.json`). A single
DingTalk robot's Stream can only be consumed by one process, so this adapter and
the OpenClaw gateway channel **must use two different DingTalk apps**:

- app #1: `channels.ddingtalk` in the gateway → conversational BlockClaw
- app #2: this adapter → the narrow queue-driver (accept / batch / status)

Point this adapter's `DINGTALK_IM_CLIENT_ID` / `DINGTALK_IM_CLIENT_SECRET` at the
**second** DingTalk app, created the same way (enterprise inner app + robot with
**消息接收模式 = Stream 模式**).

## Scope

- `query_status`
- `start_review`
- `build_draft_package`
- batch `build_draft_package` when the message names a model, market, and manual
  copy/config scope (e.g. `输出JE-1000F的所有欧规说明书文案`,
  `构建JE-1000F的所有欧规说明书文案`)
- read-only manual-index lookups from the Feishu Base table `发布文档管理`
  (e.g. `查 JE-2000F 的说明书链接`); these call `build.py manual-index-query`
  before queue resolution and never dispatch builds
- `publish` with explicit confirmation (`确认发布` / `confirm`)

## Differences from the Feishu adapter

- **Ingress**: DingTalk Stream (`dingtalk-stream` `DWClient`, topic
  `/v1.0/im/bot/messages/get`) instead of a Feishu webhook / `lark-cli`
  long connection. No webhook host/port, verification token, or encrypt key.
- **Egress**: replies go to the inbound message's `sessionWebhook` first, then
  fall back to the authenticated robot API (`/v1.0/robot/oToMessages/batchSend`
  for 1:1, `/v1.0/robot/groupMessages/send` for groups). Markdown, 4000-char
  practical limit.
- **No message reactions**: DingTalk has no reaction API, so the Feishu adapter's
  per-stage emoji reactions degrade to a single optional one-line text ack on
  receipt (`DINGTALK_IM_ACK_ON_RECEIVED`, default on). Every other stage already
  sends an explicit text reply.
- **Access control**: `DINGTALK_IM_ALLOW_FROM` (DingTalk `staffId`s, or `*`) is
  the gate. It is **fail-closed**: an empty allowlist ignores every sender. There
  is no Feishu-style chat-membership assumption.

## Environment

Required:

- `DINGTALK_IM_CLIENT_ID` (the second app's AppKey / Client ID)
- `DINGTALK_IM_CLIENT_SECRET` (the second app's AppSecret / Client Secret)
- `AUTO_MANUAL_REPO_ROOT`
- `AUTO_MANUAL_CONTROL_CONFIG`

Access control:

- `DINGTALK_IM_ALLOW_FROM`; comma-separated DingTalk `staffId`s allowed to drive
  the bot, or `*` to open it. Empty = fail-closed (ignore everyone).

Optional:

- `DINGTALK_IM_ROBOT_CODE`; defaults to `DINGTALK_IM_CLIENT_ID`
- `DINGTALK_IM_REQUIRE_MENTION`; defaults to `true` (group messages act only when
  the bot is @-mentioned, via DingTalk `isInAtList`)
- `DINGTALK_IM_ACK_ON_RECEIVED`; defaults to `true`; one-line text ack on receipt
- `DINGTALK_IM_RECEIVED_ACK_TEXT`; overrides the default `✓ 已收到，处理中…`
- `DINGTALK_IM_PUBLISH_CONFIRM_TTL_SECONDS`; defaults to `600`
- `DINGTALK_IM_CONTEXT_TTL_SECONDS`; defaults to `3600`
- `DINGTALK_IM_BATCH_DISPATCH_DELAY_MS`; defaults to `2000`
- `DINGTALK_IM_BATCH_STATUS_TIMEOUT_SECONDS`; defaults to `60`
- `DINGTALK_IM_BATCH_STATUS_POLL_SECONDS`; defaults to `5`
- `DINGTALK_IM_MANUAL_INDEX_LIMIT`; defaults to `10`
- `DINGTALK_IM_STATE_FILE`
- `DINGTALK_IM_LOCAL_PROFILE_DIR` or `OPENCLAW_LOCAL_PROFILE_DIR`
- `DINGTALK_IM_DISABLE_LOCAL_PROFILE` or `OPENCLAW_DISABLE_LOCAL_PROFILE`
- `DINGTALK_IM_API_BASE_URL`; defaults to `https://api.dingtalk.com`

The manual-index Base overrides (`FEISHU_MANUAL_INDEX_*`) are read by
`build.py manual-index-query` itself and are unchanged.

## Install and run

```bash
npm install --prefix integrations/openclaw/dingtalk-im-adapter
DINGTALK_IM_CLIENT_ID=ding... \
DINGTALK_IM_CLIENT_SECRET=... \
DINGTALK_IM_ALLOW_FROM=<your-staffId> \
AUTO_MANUAL_CONTROL_CONFIG=configs/config.us.yaml \
  npm start --prefix integrations/openclaw/dingtalk-im-adapter
```

`npm start` runs `dingtalk-stream-listener.mjs`, which opens the DingTalk Stream
connection and subscribes to robot messages. The second DingTalk app must have a
robot with **消息接收模式 = Stream 模式** and the
`企业内机器人发送消息` permission, and must be published.

## Local-only OpenClaw profile

Like the Feishu adapter, optional profile files load from `<repo>/.openclaw/`
(git-ignored): `aliases.local.json` for private phrase expansion before
`queue-resolve-action`, `reply-phrases.local.json` for reply-heading overrides,
and `persona.local.md`. (`reactions.local.json` is ignored here — DingTalk has no
reactions.) Files load at startup; restart after editing.

## Test

```bash
npm test --prefix integrations/openclaw/dingtalk-im-adapter
```

The suite covers the DingTalk-specific modules (Stream event parsing, the reply
client's sessionWebhook/robot-API routing and token caching, the received-ack
degrade) plus the shared queue orchestration through the DingTalk reply
interface. The exhaustive orchestration variations live in the Feishu adapter's
suite, since the handler core is shared.
