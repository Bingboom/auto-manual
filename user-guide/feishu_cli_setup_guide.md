# 飞书 CLI + Claude 操作云文档/多维表 配置指南

Updated: 2026-06-17

这份指南说明如何**新建一个飞书应用、在本机安装飞书 CLI（`lark-cli`）、完成授权，然后让 Claude（或本仓库的 OpenClaw/BlockClaw agent）基于 `lark-cli` 读取并操作飞书云文档 / 多维表（Bitable）**。

适用场景：

- 在一台新机器上把本仓库接到飞书 Base（phase2 数据表、`Translation_Memory`、`发布文档管理` 目录表等）
- 让 Claude 通过自然语言驱动 `lark-cli` 查询/读取多维表记录、解析 wiki 节点、读字段结构
- 给某个技能（如 [`.agents/skills/bitable-translation-memory`](../.agents/skills/bitable-translation-memory/SKILL.md)）准备底层 CLI 通道

边界：本指南只覆盖 **CLI 通道的搭建与读取操作**。写入（建表/改记录）属于受控操作，按各技能的写入流程执行，不在这里展开。更深入的 phase2 同步与对账见 [`code-as-doc/phase2_lark_setup_and_parity_plan.md`](../code-as-doc/phase2_lark_setup_and_parity_plan.md)。

---

## 0. 一次性原理

`lark-cli` 是一个本地 CLI，绑定**一个飞书应用（app）**，并持有两种身份：

- **bot（应用身份）**：用应用自身的 token。**读取多维表记录必须用 bot 身份**（`--as bot`）——普通用户身份通常缺 `base:record:retrieve` 等 scope。
- **user（用户身份）**：用扫码登录的个人授权，覆盖面更广（云文档、wiki、云盘等），但读 Base 记录会因缺 scope 失败。

Claude 不直接调飞书 API，而是通过 `Bash` 工具运行 `lark-cli ...` 命令、解析返回的 JSON。所以本机只要 `lark-cli` 装好、授权好，Claude 就能操作飞书。

---

## 1. 前置：Node + npm

`lark-cli` 通过 npm 全局安装，需要 Node.js。

macOS（Homebrew）：

```bash
brew install node
node --version    # 期望 v20+，本指南实测 v26
npm --version
```

如果 `node`/`npm` 装好后 shell 找不到，确认 `/opt/homebrew/bin` 在 `PATH` 中。

---

## 2. 安装飞书 CLI

```bash
npm install -g @larksuite/cli
lark-cli --version    # 例：lark-cli version 1.0.51
```

---

## 3. 新建/配置应用

`config init --new` 会注册一个新应用并把配置写到本机 `~/.lark-cli/`。它是**阻塞命令**：会打印一个验证链接（同时输出一个二维码），需要在浏览器里打开完成应用注册。

```bash
lark-cli config init --new
```

操作要点：

- 命令输出形如 `https://open.feishu.cn/page/cli?user_code=XXXX-XXXX&...` 的链接，**在浏览器打开并按提示完成应用配置**。
- 在 agent/无人值守环境里，这条命令最长阻塞约几分钟。Claude 的做法是：**把命令放后台运行**，从输出文件里取出验证链接发给操作者，操作者完成后命令自动返回。
- 配置成功后再看一次状态，应能看到应用 `appId` 以及 **bot 身份 = ready**：

```bash
lark-cli auth status
```

> 同机要保留旧应用时：先设置独立的配置目录（如本仓库 Feishu IM adapter 用的 `FEISHU_IM_LARK_CLI_HOME`），再为新应用 `config init`，避免覆盖默认 `~/.lark-cli`。

---

## 4. 用户登录（user 身份）

如果还要用 user 身份操作云文档/wiki，再做一次交互登录：

```bash
lark-cli auth login --recommend
```

操作要点：

- 同样会输出一个验证链接（`https://accounts.feishu.cn/oauth/v1/device/verify?...`）。在浏览器打开或用飞书 App 扫码完成授权。
- 需要二维码图片时：

  ```bash
  lark-cli auth qrcode '<上面的 verification_url>' --output ./qr.png
  ```

  注意 `--output` **只接受当前目录下的相对路径**（不接受 `/tmp/...` 这类绝对路径）。

- agent 环境下同样建议后台运行：先把链接发给操作者，等其完成授权后命令自动返回。user token 有有效期，过期后重跑 `lark-cli auth login` 即可。

---

## 5. 验证授权

```bash
lark-cli auth status
```

确认 `identities.bot.status` 和（如登录了）`identities.user.status` 都是 `ready`。`tokenStatus: valid` 表示可用，`expiresAt` 是过期时间。

---

## 6. Claude 基于 lark-cli 操作云文档/多维表

下面是 Claude 实际会用到的命令模式。核心约定：

- **读多维表记录一律加 `--as bot`**。
- `api GET` 用 `--params '<json>'` 传查询参数；`api POST` 用 `--data '<json>'` 传请求体。
- 多维表 app（Base）由一个 **app token** 标识，但分享链接给的是 **wiki 节点 token**；先把 wiki 节点解析成 app token 再操作。**wiki 节点在 Base 被复制后保持不变，app token 会变**，所以优先用 wiki 节点定位。

### 6.1 从分享链接定位一张表

一个多维表分享链接形如：

```
https://<tenant>.feishu.cn/wiki/<WIKI_NODE>?table=<TABLE_ID>&view=<VIEW_ID>
```

把 wiki 节点解析成 Base 的 app token：

```bash
lark-cli api GET /open-apis/wiki/v2/spaces/get_node \
  --params '{"token":"<WIKI_NODE>","obj_type":"wiki"}' --as bot
# 返回 data.node.obj_token 即 Base app token
```

### 6.2 列出表 / 字段

```bash
# 列出 Base 内所有表
lark-cli base +table-list --base-token <BASE_TOKEN> --as bot

# 列出某张表的字段（字段名 + 类型）
lark-cli api GET /open-apis/bitable/v1/apps/<BASE_TOKEN>/tables/<TABLE_ID>/fields \
  --params '{"page_size":100}' --as bot
```

### 6.3 读记录（搜索 / 分页）

```bash
lark-cli api POST /open-apis/bitable/v1/apps/<BASE_TOKEN>/tables/<TABLE_ID>/records/search \
  --data '{"view_id":"<VIEW_ID>","page_size":100}' --as bot
```

返回 `data.items[*].fields` 是记录字段；`data.has_more` + `data.page_token` 用于翻页（把上一次的 `page_token` 放进下一次 `--data`）。

### 6.4 字段值的形态

多维表字段值类型不统一，解析时要做归一化：

- 文本：`[{"text": "...", "type": "text"}]` 或纯字符串
- 单选：`"PVT"`
- 多值/关联：`["JE-2000F", ...]`
- 链接（URL 字段）：`{"link": "https://...", "text": "锚文本"}`
- 日期：毫秒时间戳，如 `1777219200000`

本仓库已有可参考的自包含解析脚本：[`.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py`](../.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py)（翻译记忆查询，含 wiki 节点解析与字段归一化）。新接一张表时，照它的 wiki 节点解析 / 字段值归一化 / `--as bot` 模式改即可。

### 6.5 在飞书聊天里回链接

往飞书发链接时，渲染成 Markdown 链接（`[文档名](https://...)`）才会显示成可点击的文档卡片；直接贴裸 URL 不会渲染成卡片。

---

## 7. 安全与规范

- **不要把 app token / base token / 表 ID 硬编码进通用逻辑**；用环境变量或脚本的可覆盖默认值（参考 `FEISHU_PHASE2_*`、`FEISHU_PUBLISHED_DOCS_*` 等命名），并优先用稳定的 wiki 节点解析 base token。
- 默认只做**读取**。写入（建表、改字段、写记录）走对应技能的受控流程，并先确认目标。
- 代码改动一律落在 `auto-manual` 源仓库；`Hello-Docs` 是单向镜像，不在镜像里改代码。

---

## 8. 故障排查

| 现象 | 原因 / 处理 |
| --- | --- |
| 读记录报 `missing_scope` / `base:record:retrieve` | 用了 user 身份。加 `--as bot` 重试。 |
| `auth status` 显示 `not_configured` | 还没 `lark-cli config init --new`。 |
| user `tokenStatus` 过期 | 重跑 `lark-cli auth login`，重新扫码/授权。 |
| `config init` / `auth login` 超时作废 | 验证链接每次重启都会失效；后台运行一次、把链接发出去、等操作者完成，不要短超时反复重试。 |
| `--output` 报 unsafe path | `auth qrcode --output` 只接受当前目录相对路径。 |
| `node`/`lark-cli` command not found | 确认 `/opt/homebrew/bin` 在 `PATH`，或重开 shell。 |

---

## 9. 参考

- [`code-as-doc/phase2_lark_setup_and_parity_plan.md`](../code-as-doc/phase2_lark_setup_and_parity_plan.md)：phase2 同步与 phase1/phase2 对账
- [`.agents/skills/bitable-translation-memory/SKILL.md`](../.agents/skills/bitable-translation-memory/SKILL.md)：翻译记忆查询技能（多维表读取脚本范例）
- [`user-guide/hello_auto-doc.md`](hello_auto-doc.md)：当前人工工作流总览
