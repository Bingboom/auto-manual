# 钉钉 BlockClaw 机器人配置指南(复刻到新主机)

把"在钉钉里私聊 / 群里 @机器人 → BlockClaw(OpenClaw 智能体,带人格)→ 驱动 auto-manual 的查询 / 构建 / 发布"这套配置,复刻到一台新主机(例如公司主机,工作目录是本仓库的镜像)。

## 架构(一句话)

钉钉企业机器人(**Stream 长连接**)→ OpenClaw 网关的 `channels.ddingtalk` 通道(由社区插件 `@largezhou/ddingtalk` 提供)→ 路由到 **BlockClaw 智能体**。

- 无需公网 IP / 回调 URL(Stream 长连接);
- 无需额外常驻进程 —— 随 OpenClaw 网关一起跑;
- 人格、群@、自然对话都由 BlockClaw(LLM)原生提供。

## 前提

1. 新主机上 **OpenClaw 网关 + BlockClaw 智能体已在运行**(即飞书那套 `channels.feishu` 已工作,工作目录指向本仓库镜像)。本文只新增钉钉通道;若 OpenClaw 尚未搭好,先跑 `openclaw onboard` 完成网关 / workspace / BlockClaw 基础配置,再回到这里。
2. OpenClaw 版本 ≥ `2026.3.22`(插件 peer 要求;开发时用的是 `2026.4.10`)。用 `openclaw --version` 查。
3. 你在该主机所属**钉钉组织**里的账号(用来 @机器人并加入白名单)。

> ⚠️ **不要照抄个人机的值。** Client ID、Client Secret、你的 `staffId` 在公司那套都是新的(尤其 `staffId` 是按钉钉组织区分的)。下面用占位符,按步骤取真实值。

需要在本主机替换的值:

| 占位符 | 含义 | 怎么拿 |
| --- | --- | --- |
| `<CLIENT_ID>` | 钉钉应用 AppKey / Client ID | 步骤 2 |
| `<CLIENT_SECRET>` | 钉钉应用 AppSecret / Client Secret | 步骤 2 |
| `<YOUR_STAFF_ID>` | 你的钉钉 staffId(白名单) | 步骤 4(日志法) |

---

## 步骤 1 — 安装钉钉通道插件

```bash
openclaw plugins install @largezhou/ddingtalk
```

确认已加载:

```bash
openclaw plugins inspect ddingtalk
# 期望:status: loaded, kind: channel, channelIds: ["ddingtalk"]
```

（可选硬化:`openclaw.json` 里设 `plugins.allow: ["ddingtalk", ...]`,把第三方插件钉成显式信任,消除 `plugins.allow is empty` 提示。）

## 步骤 2 — 建钉钉企业应用 + 机器人

在钉钉开发者后台:`https://open-dev.dingtalk.com/fe/app`

1. **创建应用** → 进入 **凭证与基础信息** → 复制 **Client ID**(形如 `dingxxxx`)和 **Client Secret**。
2. **添加应用能力 → 机器人 → 添加**。
3. ⭐ 机器人配置里 **消息接收模式 = Stream 模式**(关键;不选 Stream 收不到消息)。
4. **权限管理**开通:
   - `企业内机器人发送消息`
   - `根据 downloadCode 获取机器人接收消息的下载链接`(收图片用)
5. ⭐ **发布机器人版本**(创建版本 → 填可用范围 → 确认发布)。

> 🔴 **最容易踩的坑**:机器人**没发布**或**没选 Stream 接收模式**时,即使网关日志显示 `connect success`,私聊也**不会投递**进来,表现为机器人完全静默。一定要先在后台确认"已发布版本 + Stream 接收模式 + 权限齐全"。

## 步骤 3 — 配置 `channels.ddingtalk`

编辑 `~/.openclaw/openclaw.json`,在 `channels` 下新增 `ddingtalk`(保留已有的 `channels.feishu` 等不要动):

> 仓库模板可直接参考:`integrations/openclaw/openclaw.ddingtalk.example.json`(只加钉钉通道,合并进现有配置);或 `integrations/openclaw/openclaw.example.json`(整份脱敏网关配置,含 agents/feishu/hooks/plugins,用于全新主机复刻整个 BlockClaw)。后者里 `gateway.auth.token` 等通常由 `openclaw onboard` 生成,`wizard` / `meta` / `plugins.installs` 是自动维护项、模板已省略;所有 secret/token/id 均为占位符,填你本机的值。

```json
"ddingtalk": {
  "enabled": true,
  "clientId": "<CLIENT_ID>",
  "clientSecret": "<CLIENT_SECRET>",
  "allowFrom": [],
  "groupPolicy": "open"
}
```

要点:

- `clientSecret` **必须是明文字符串**。钉钉**不在** OpenClaw 的 SecretRef 凭证白名单内(那是给飞书 / Slack 等内置渠道的),写成 `{ "source": "file", ... }` 引用会报 `channels.ddingtalk.clientSecret: invalid config: must be string`,导致整份配置失效。明文存 `openclaw.json` 即可(该文件本就含明文 `gateway.auth.token`);建议给该文件 `chmod 600`。
  - 不想在 `openclaw.json` 里放明文,也可改用环境变量 `DINGTALK_CLIENT_ID` / `DINGTALK_CLIENT_SECRET`(设在网关进程环境里),`clientId/clientSecret` 留空。
- ⚠️ `allowFrom` **留空 / 不设 = 对所有人开放**(插件默认 `["*"]` = 允许所有人,不是 fail-closed)。要真正限制访问,**必须**在 `allowFrom` 里列出具体 staffId;不在名单里的人会被忽略(不回复),但消息**仍会记进日志**。本步骤先留空只是为了步骤 4 用日志法收集 staffId,届时机器人对任何人都会回复 —— 拿到 staffId 后务必回填收口。
- `allowFrom[0]`(列表第一个 staffId)同时是 `openclaw send` 主动推送的默认目标。
- `groupPolicy: "open"` = 支持群聊 @(把机器人拉进群、@它即可)。不想要群聊就设 `"disabled"`。

## 步骤 4 — 拿到你的 staffId 并锁定白名单

`staffId` 是机器人实际看到的发件人标识(形如 `1234567890-1234567890` 这样的复合 ID,此处仅为占位示例),按钉钉组织区分。最稳的取法是"让机器人记一笔日志":

1. 先重启网关让上面的配置生效:`openclaw gateway restart`
2. 在钉钉里**私聊该机器人**发一句(如 `hi`)。此时 `allowFrom` 仍为空 = 对所有人开放,所以机器人**会回复你** —— 这是收集 staffId 阶段的正常现象,不代表已经收口。
3. 读网关日志找发件人 staffId(无论机器人是否回复,入站消息都会记进日志):
   ```bash
   openclaw channels logs --channel ddingtalk
   ```
   或在网关日志文件里搜 `收到消息`(日志路径见 `openclaw gateway status` 的 `File logs`),日志会带 `昵称(staffId)`。
4. 把取到的值填进 `openclaw.json` 的 `allowFrom`,然后 `openclaw gateway restart` 收口 —— 在你填入具体 staffId 之前,机器人对所有人开放:
   ```json
   "allowFrom": ["<YOUR_STAFF_ID>"]
   ```

> 也可在钉钉管理后台 / 通讯录查 userid,但日志法拿到的就是机器人实际比对的值,最不容易错。
> 团队群里想让其他人也能驱动:把他们的 staffId 一并加进 `allowFrom`(同样用日志法收集)。

## 步骤 5 — 重启网关并验证

```bash
openclaw gateway restart          # ⚠️ 飞书 bot 会断几秒重连;挑空档执行
openclaw channels status          # 期望 Feishu 和 DingTalk 都 running
openclaw channels logs --channel ddingtalk   # 期望看到 connect success(可能在原始日志里,不在 channel 过滤视图)
```

## 步骤 6 — 测试

- 私聊机器人发 `你是谁` → 应是 **BlockClaw 的人格回复**(自然语气),而非模板。
- 把机器人**拉进一个群**,在群里 **@它** 发一句 → 群里回应。
- 让它干活(自然语言):如 `查 JE-1000F_US`、`构建JE-1000F的所有欧规说明书文案`、`发布 …`。BlockClaw 会判断并触发对应的 auto-manual 流程。

---

## 排错(本次踩过的坑)

| 现象 | 原因 / 解决 |
| --- | --- |
| 机器人完全静默,网关日志无入站消息 | 机器人没发布 / 消息接收模式≠Stream / 缺权限。回后台确认"已发布 + Stream + 权限"。`connect success` 不代表能收消息。 |
| `clientSecret: invalid config: must be string` | secret 写成了对象引用。改成明文字符串(钉钉不在 SecretRef 白名单)。 |
| 你私聊有反应,但群里别人 @没用 | `allowFrom` 只放了你。把其他人 staffId 也加进去。 |
| 任何人都能驱动机器人(本想只放自己) | `allowFrom` 还留空 = 对所有人开放(默认 `["*"]`,不是 fail-closed)。填入具体 staffId 后 `openclaw gateway restart` 收口;不在名单的人会被忽略,但仍记日志。 |
| 群里 @不回 | 机器人没被拉进该群 / `groupPolicy: "disabled"` / 你的 staffId 不在名单。 |
| 启动后看到 `plugins.allow is empty` | 可选硬化:设 `plugins.allow: ["ddingtalk", ...]`。 |
| 重启网关后飞书短暂掉线 | 正常,几秒重连。 |

## 回滚

改 `openclaw.json` 前网关安装 / 本流程都会留备份(如 `openclaw.json.bak*`)。要移除钉钉通道:删掉 `channels.ddingtalk` 块并 `openclaw gateway restart`;要卸载插件:`openclaw plugins uninstall ddingtalk`。

## 附:仓库里的"独立适配器"(可选,非本方案)

仓库另有 `integrations/openclaw/dingtalk-im-adapter/` —— 一个**确定性**的钉钉 Stream 监听器,提供自动回执、批量派发、状态轮询,**不经过 LLM / 没有人格**。本方案没用它(选的是 BlockClaw 人格路线)。如果以后需要"机械、确定的批量队列驱动",它是现成备选:

- `npm install --prefix integrations/openclaw/dingtalk-im-adapter` 后 `npm start --prefix integrations/openclaw/dingtalk-im-adapter`;
- 必须用**另一个**钉钉应用(同一个机器人的 Stream 不能被网关通道和适配器同时消费);
- 配置见该目录下的 `README.md`。
