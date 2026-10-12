# Workflow guide: OpenClaw, Feishu IM, DingTalk and Wukong

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

### 钉钉查询欧规产品信息

在已启用查询功能的 BlockClaw 中，直接问“JE-2000F 欧规 USB-C 输出功率是多少？”
或“JE-2000F 节能模式怎么关闭？”。机器人读取已发布说明书，回答应附型号、EU、
版本和原文章节链接。型号不明确会先确认；未找到依据会说明未命中。
默认检索英文来源，用中文解释；旧版语言范围未验证时会明确标记。

固定入口 `/manual-query JE-2000F USB-C输出` 返回章节链接和检索片段；完整操作
请继续提问或打开原文。所有已发布 EU 版本自动随 RTD 构建进入索引；新增型号无需
单独配置。图片目前仅使用已有 alt 文字，复杂接线图仍需查看原文。
现有机器人只需更新控制插件并设置站点地址，具体见
[启用与验收](../../code-as-doc/dev/eu_manual_query.md#activation-on-the-existing-gateway)。

### 1.3 DingTalk Wukong MCP Bridge

The version-controlled Wukong bridge lives at
[`agent/wukong-bridge/`](../../agent/wukong-bridge). Do not maintain a second
untracked source copy under a home-directory `wukong-bridge` folder. Point the
MCP registration at the checked-in `server.py`, keep authentication in the
external `lark-cli` profile, and keep runtime jobs/exports under the external
state directory described in the bridge README.

For KR source intake, Wukong must pass an explicit sibling target to both
`intake_stage` and `intake_commit`. Staging validates canonical English source
text and the sibling identity
`Page + Row_key + Slot_key + Section + Line_order`; formal intake additionally
requires complete coverage of both `规格参数明细` and `页面占位参数`. A successful
partial staging response is not a complete target: inspect
`coverage_missing_rows`, finish the missing structures, review every value in
Base, and use the existing checkbox plus explicit-chat approval gates before
formal intake. Full configuration and the current contract version are in
[`agent/wukong-bridge/README.md`](../../agent/wukong-bridge/README.md).

   - for future app-only DingTalk provider research, [`../tools/dingtalk/spike_cli.py`](../../tools/dingtalk/spike_cli.py) is the manual Phase 0 smoke helper; it gets an App-Only token by default, then lets you supply the exact DingTalk list/update/upload endpoints for the chosen product without changing the current queue runtime
   - [`../tools/dingtalk/auth.py`](../../tools/dingtalk/auth.py) now wraps the verified App-Only token flow behind `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, and `DINGTALK_CORP_ID`, and [`../tools/dingtalk/workspace.py`](../../tools/dingtalk/workspace.py) can already extract a target docs node ID from a standard `alidocs.dingtalk.com/i/nodes/...` URL

 - `python build.py queue-query --config configs/config.us.yaml --queue-scope all --task-id "JE-1000F_US_0.3_Build Draft Package" --json` is the recommended local Phase 2 lookup before a natural-language OpenClaw action; it resolves the exact Feishu row and returns the `record_id`, `Task_id`, `Workflow_action`, `Git_ref`, `构建结果`, and the phase-aware `delivery_kind / delivery_url / delivery_ready` contract
 - `python build.py queue-resolve-action --config configs/config.us.yaml --query-text "发布 JE-1000F_US_0.3" --json` is the structured dry-run resolver for the control layer; it returns the bounded `action_name`, `resolution_status`, confirmation requirement, and matched row fields before any dispatch happens
 - for a fixed "现在库里构建了多少文档" lookup, run `python build.py queue-query --config configs/config.us.yaml --queue-scope document-link --result-contains success --limit 200 --json` and the same command with `configs/config.ja.yaml`, then count rows whose `normalized_workflow_action` is `draft` or `publish`; natural-language asks such as `当前所有已构建文档链接` now resolve to the same successful `Document_link` surface with a larger default limit
 - inside this repo, the OpenClaw-backed assistant is named **BlockClaw** because it works with content blocks; treat it as the default document-build operator that helps you build, review, publish, inspect queue rows, and explain failures for `auto-manual`, with translation and copy work acting as supporting helpers

 - [`../integrations/openclaw/feishu-im-webhook-adapter/`](../../integrations/openclaw/feishu-im-webhook-adapter/) is the repo-external Feishu IM webhook adapter for this control layer; it receives Feishu text messages, calls `queue-resolve-action|queue-query|queue-execute`, and replies back into the same Feishu thread
 - cloud-doc review backport is **not** an IM/BlockClaw capability — its LLM target-resolution is too uncertain for chat. Run it from Claude Code / Codex / a terminal via `python -m tools.backport.cloud_doc run-review-branch ...` (see the backport step below and AGENTS.md §3)
 - the adapter reads optional local-only profile files from `.openclaw/` for private aliases, reply phrasing, and Feishu message reaction choices; keep personal memory, real chat samples, and custom wording there instead of committing them to remote
 - set `FEISHU_IM_ENABLE_MESSAGE_REACTIONS=true` only after the Feishu app has message reaction permission; reactions are best-effort, the initial received-stage reaction defaults to `Get`, and the same-thread text reply remains the reliable status surface
 - when the live desktop entrypoint is the installed OpenClaw gateway rather than the repo adapter, run [`../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs`](../../integrations/openclaw/scripts/patch_openclaw_feishu_received_reaction.mjs) before `openclaw gateway` starts; it adds the native Feishu `Get` reaction directly inside the `im.message.receive_v1` handler, before agent reasoning, table lookup, or build dispatch; it supports both the legacy bundled-`dist/` install and the OpenClaw ≥ 2026.6 `@openclaw/feishu` plugin layout under `~/.openclaw/npm/projects/openclaw-feishu-*/`
 - `python build.py listen-message-control --config configs/config.us.yaml` is the no-server local Feishu IM entry for the same control layer; it listens to `im.message.receive_v1` through `lark-cli` and replies in-thread without exposing a public callback URL
 - if the same machine must keep the old Feishu app for local phase2 operations, set `FEISHU_IM_LARK_CLI_HOME` before starting `listen-message-control`; that makes the new app use its own isolated `lark-cli` home instead of rewriting the default `~/.lark-cli`
 - for a long-lived ECS host, use the adapter `systemd` deployment assets under [`../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/`](../../integrations/openclaw/feishu-im-webhook-adapter/deploy/systemd/); the wrapper script sources the same `env.sh` you already use for manual startup
 - the same `queue-query --query-text` parser also understands `Task_id` strings such as `JE-1000F_US_0.3_Build Draft Package`, spaced asks like `帮我生成 JE-1000F US 0.3 草稿`, document-key-only review asks like `review JE-1000F_EU`, `开始 review JE-1000F us-merged`, and `为什么 JE-1000F US 0.3 构建失败`; if it can derive an exact `Task_id`, that selector takes priority
 - OpenClaw can also resolve config-scoped batch Draft asks such as `输出JE-1000F的所有欧规说明书文案`, `构建JE-1000F的所有欧规说明书文案`, `基于配置构建JE-1000F的欧规`, or the implicit-all form `构建JE-1000F的欧规说明书文案`; it maps `欧规` into a `Task_id` prefix like `JE-1000F_EU_`, keeps only `Build Draft Package` rows with `是否触发文档构建` enabled, and dispatches those rows by Feishu `record_id`. Draft and print Publish share a Document_link record concurrency slot; Web Publish uses one global publish-branch transaction slot. `是否强制刷新数据` remains the print/draft row-level input, while Web Publish always refreshes approved assets.

 - exact OpenClaw Build Draft Package / Publish dispatches require the selected row's `是否触发文档构建` to be enabled; unchecked rows fail fast instead of launching a GitHub run that exits without output.
 - status-like asks such as `草稿包好了没`, `这个跑完了吗`, or `这个到哪了` resolve as status checks even when they mention draft/publish wording; pronoun follow-ups can reuse the last resolved `record_id` from the local adapter state, but build/trigger/rerun requests always resolve fresh from the current Feishu table instead of appending a remembered `record_id`
 - retry-style asks such as `补跑英语和法语`, `补构建法语`, or `重试这个` are treated as Build Draft Package intent; the adapter reuses only safe context such as model, market, version, and Git_ref, then resolves fresh queue rows instead of reusing the previous `record_id`
 - `queue-query` and `queue-resolve-action` accept `--langs en,fr` for bounded multi-language selection; natural-language asks can also use the registered Chinese/English aliases such as `英语`, `法语`, `西语`, `德语`, `意语`, and `日语`. Display labels and query aliases come from `tools/lang_registry.py`, so new language coverage is added at the registry rather than in each consumer. The fake `xx` end-to-end probe verifies that the same registry row flows through sync, localized copy, content lint, queue query, and preview labels; reference-bound IDML registration remains separately approved.

 - `queue-query`, `queue-resolve-action`, and `queue-execute` accept `--fresh-since <iso-or-epoch>` so status replies can distinguish this-run writeback from older row results; Document_link JSON rows include `freshness_status`, `result_built_at`, `result_is_fresh`, and `build_started_at`
 - `queue-query --json` includes `matched_count`, `returned_count`, `limit`, and `truncated`; if a broad query hits the default limit, treat `truncated=true` as an incomplete answer and re-run with narrower filters or a higher `--limit`
 - broad latest-link asks such as `构建好的文档链接发我` return successful latest-version rows per `Document_Key`, while inventory asks such as `当前所有已构建文档链接` keep all successful rows up to the larger inventory limit
 - batch delivery replies in Feishu IM are sent as one status summary plus one message per `delivery_url`; short follow-ups such as `发` or `发一下` reuse the previous batch context and resend those phase-aware links instead of flattening them into one plain-text block
 - adapter conversation memory is never the build truth source: `这个好了没` re-reads Feishu by `record_id`, and if a remembered row has been deleted or moved, BlockClaw reports it as not found and clears that context instead of replaying the old row
 - `python build.py queue-execute --config configs/config.us.yaml --query-text "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。只返回 record_id、Git_ref、构建结果和 delivery_url。"` is the recommended deterministic execution entry for natural-language OpenClaw build asks; it resolves the Feishu row, dispatches the matching `main`-owned workflow, waits for completion, and then re-reads the Feishu row before returning the final fields plus `accepted_at`, `run_id`, `run_url`, and `freshness_status`. OpenClaw must not first run local `check` / `word` / `sync-data` or inspect `data/phase2/*.csv`; the remote worker owns the row's `是否强制刷新数据` behavior.
 - if the GitHub run finishes but the Feishu row still only has a pre-dispatch `FAILED` or `SUCCESS`, OpenClaw reports `freshness_status=stale_result` or `writeback_pending` instead of treating that old row value as the current run result
 - a local observation gap is never reported as an action failure: once GitHub accepts a dispatch, a transient `status`/poll error, a `control-layer ... fetch failed`, or a wait-deadline timeout makes `queue-execute` defer to the authoritative Feishu/Base writeback (`freshness_status`) instead of raising — it reports a failure only when the GitHub run reaches a genuine terminal failure **and** the row is still not fresh; `/manual-status` likewise returns the last known run state plus an `observation_error` line rather than erroring out, because the remote run keeps going regardless of whether the local poller could read it back
 - builds report results on an accept-first lifecycle, never by holding the chat turn open: the dispatch reply and `/manual-status` carry `state: accepted|processing|completed|failed` plus a `note:` pointing back to `status last`, so an in-flight run reads as `任务正在处理中` (not a failure). On the Feishu IM adapter a single-record build replies "已受理（处理中）" immediately, dispatches with `--no-wait`, and does **not** poll; progress is delivered **on demand** — when you re-ask "这个好了没", the adapter reads the authoritative state at that moment (a fresh Base writeback wins → `已完成`/`失败`; otherwise it reads the live GitHub run once via the remembered `run_id` → 仍在跑=`处理中`, run 已失败但未写回=`失败`, run 完成但结果未落表=`处理中`) and answers 处理中/已完成/失败. Single read per question, not polling
 - against the Feishu message control plan, the repo now has the full repo-local Phase 2 stack: query, deterministic execute, structured failure replies, explicit Publish confirmation, and a standalone Feishu IM webhook adapter are all live. Encrypted callback support and ECS deployment assets are now repo-owned; the remaining gaps are shared state and a stable named ingress rollout.
 - if you keep using `trycloudflare.com`, only the process restart becomes stable; the callback URL itself still changes after a tunnel restart. For a stable URL, switch the same adapter to a named Cloudflare Tunnel or another fixed HTTPS ingress
 - if `queue-execute` resolves `Workflow_action = Publish`, add `--confirm-publish`; otherwise it now stops before dispatch
 - repo-local OpenClaw dispatch no longer treats `adm-zip` as a required local install just to send a Build Draft Package or Publish dispatch from ECS; metadata artifact parsing is now best-effort, so missing package installs degrade status detail instead of blocking dispatch

 - `queue-execute` treats a `Start Review` row that already has `Review_status=InReview` and `Git_ref` as completed and returns the current row without dispatching another Action; otherwise OpenClaw dispatches `start-review`, `build-draft`, and `publish` with the resolved Feishu `record_id` so the GitHub run and final writeback stay tied to that exact queue row

 - for a multi-target build (several targets at once, or one model across regions), use `queue-execute --allow-multiple`. It validates every matching row, runs the same warning-only target-bound asset preflight for each Draft/Publish row, then starts one batch worker run per queue action with the exact eligible record set, so the third pending target cannot be silently lost or accidentally replaced by another pending row. The command returns a per-record JSON report (`matched_count` / `dispatched_count` / `skipped_count` / `error_count` + `results` with `record_id`/`run_id`/`status`/`reason`/`asset_preflight`); all dispatched rows from one action share the same `run_id`. It is accept-first (no completion wait). Report only rows returned as `dispatched` (with a `run_id`) as actually started — never infer "已进队" from the trigger flag — and ask for a complete target name (e.g. `JE-1000F_CN_1.3`, not `JE-1000F_CN`) when a version is missing
