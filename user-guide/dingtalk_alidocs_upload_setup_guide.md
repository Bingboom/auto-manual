# 钉钉知识库上传路径配置指南

Updated: 2026-04-14

这份指南说明当前仓库如何把构建好的 `.docx` 上传到钉钉知识库目录，并把生成后的钉钉节点链接回写到 Feishu `Document_link`。

当前实现边界：

- 队列控制面仍然在 Feishu
- phase2 结构化数据仍然从 Feishu 读取
- `Document_link` 状态和链接仍然回写到 Feishu
- 文档产物仍先上传到 Feishu/wiki，随后可把同一份 DOCX 同步到 DingTalk AliDocs

当前上传方案是浏览器会话模式，不是正式公开 OpenAPI 模式。
它基于当前已验证的 AliDocs 上传链路：

1. `uploadinfo`
2. OSS 对象上传
3. `commit`
4. 生成 DingTalk 节点链接

## 1. 需要准备什么

本地至少要有：

- 已可用的 Feishu phase2 环境变量
- 已安装并可用的仓库 `.venv`
- 已登录的 DingTalk AliDocs 网页会话
- 一个可上传的目标知识库目录 URL

当前相关脚本：

- [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1)
- [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1)
- [`../scripts/process_build_queue_dingtalk.ps1`](../scripts/process_build_queue_dingtalk.ps1)

当前 DingTalk 上传 helper：

- [`../tools/dingtalk/alidocs_session.py`](../tools/dingtalk/alidocs_session.py)
- [`../tools/dingtalk/alidocs_session_upload_cli.py`](../tools/dingtalk/alidocs_session_upload_cli.py)

## 2. 需要配置的环境变量

切到 DingTalk 上传时，需要这 4 个核心变量：

- `DINGTALK_DOCS_TARGET_NODE_URL`
- `DINGTALK_DOCS_A_TOKEN`
- `DINGTALK_DOCS_XSRF_TOKEN`
- `DINGTALK_DOCS_COOKIE`

可选变量：

- `DINGTALK_DOCS_BX_V`
- `AUTO_MANUAL_DINGTALK_SESSION_ROOT`

变量含义：

- `DINGTALK_DOCS_TARGET_NODE_URL`
  目标知识库目录页面 URL。上传后的文档会落到这个目录下。

- `DINGTALK_DOCS_A_TOKEN`
  浏览器请求头里的 `a-token`。

- `DINGTALK_DOCS_XSRF_TOKEN`
  浏览器请求头里的 `x-xsrf-token`。

- `DINGTALK_DOCS_COOKIE`
  上传请求里的整段 `Cookie` header。必须是完整 cookie 字符串，不是只取其中一个 cookie。

- `DINGTALK_DOCS_BX_V`
  浏览器请求头里的 `bx-v`。不填时代码会使用默认值，通常不需要手动设置。

- `AUTO_MANUAL_DINGTALK_SESSION_ROOT`
  可选的操作员会话目录。若队列表格里有 `operator_union_id`，worker 会优先查找
  `<session_root>/<operator_union_id>.json`，找不到时才回退到全局 `DINGTALK_DOCS_*`。

## 3. 目标目录 URL 怎么拿

打开你的钉钉知识库目录页面，地址栏里的 URL 就可以直接作为：

- `DINGTALK_DOCS_TARGET_NODE_URL`

例如：

```text
https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space
```

规则：

- 这应该是“目录节点”URL，不是单个已上传文档的 URL
- 当前脚本会从这个 URL 中解析出目标 `node_id`
- 上传后的新文件会作为这个目录下的新节点写入

## 4. 会话值怎么抓

### 4.1 打开浏览器抓包

1. 打开钉钉知识库目标目录页面
2. 按 `F12`
3. 打开 `Network`
4. 勾选 `Preserve log`
5. 在过滤框输入 `box/api/v2/file`

### 4.2 触发一次真实上传

1. 往该目录手动上传一个测试 `.docx`
2. 在请求列表里找到：
   - `uploadinfo`
   - `commit`

这两条请求足够拿到当前会话所需值。

### 4.3 取值位置

从 `uploadinfo` 或 `commit` 这类请求的请求头中取：

- `a-token` -> `DINGTALK_DOCS_A_TOKEN`
- `x-xsrf-token` -> `DINGTALK_DOCS_XSRF_TOKEN`
- `cookie` -> `DINGTALK_DOCS_COOKIE`
- `bx-v` -> `DINGTALK_DOCS_BX_V`

你可以直接在浏览器里：

1. 左侧点中 `uploadinfo` 或 `commit`
2. 右侧看 `Headers`
3. 在 `Request Headers` 里复制这些值

## 5. 当前窗口临时配置

如果你只想先试一次，直接在当前 PowerShell 里设置：

```powershell
$env:DINGTALK_DOCS_TARGET_NODE_URL='https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space'
$env:DINGTALK_DOCS_A_TOKEN='你的a-token'
$env:DINGTALK_DOCS_XSRF_TOKEN='你的x-xsrf-token'
$env:DINGTALK_DOCS_COOKIE='你的完整cookie'
```

如果你确实需要覆盖默认 `bx-v`，再加：

```powershell
$env:DINGTALK_DOCS_BX_V='2.5.36'
```

这种方式只对当前窗口生效。关闭 PowerShell 后就失效。

## 6. 用户级长期配置

如果你希望每次新开 PowerShell 都能直接用，把它们写成用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable('DINGTALK_DOCS_TARGET_NODE_URL', 'https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY?utm_scene=team_space', 'User')
[Environment]::SetEnvironmentVariable('DINGTALK_DOCS_A_TOKEN', '你的a-token', 'User')
[Environment]::SetEnvironmentVariable('DINGTALK_DOCS_XSRF_TOKEN', '你的x-xsrf-token', 'User')
[Environment]::SetEnvironmentVariable('DINGTALK_DOCS_COOKIE', '你的完整cookie', 'User')
```

可选：

```powershell
[Environment]::SetEnvironmentVariable('DINGTALK_DOCS_BX_V', '2.5.36', 'User')
[Environment]::SetEnvironmentVariable('AUTO_MANUAL_DINGTALK_SESSION_ROOT', "$HOME\\.auto-manual\\dingtalk-sessions", 'User')
```

写入后：

1. 关闭当前 PowerShell
2. 新开一个 PowerShell
3. 再执行队列脚本

## 7. 怎么检查变量有没有配成功

在新的 PowerShell 里执行：

```powershell
Get-ChildItem Env:DINGTALK_DOCS_*
```

至少应该看到：

- `DINGTALK_DOCS_TARGET_NODE_URL`
- `DINGTALK_DOCS_A_TOKEN`
- `DINGTALK_DOCS_XSRF_TOKEN`
- `DINGTALK_DOCS_COOKIE`
- 如果你准备按操作员切换会话，还应该看到 `AUTO_MANUAL_DINGTALK_SESSION_ROOT`

## 7.1 操作员会话文件模式

如果你不想让所有队列记录共用一套全局 DingTalk 会话，可以改用“按操作员会话文件”：

1. 先设置 `AUTO_MANUAL_DINGTALK_SESSION_ROOT`
2. 在该目录下按 `operator_union_id` 放 JSON 文件，例如：

```text
%USERPROFILE%\.auto-manual\dingtalk-sessions\alice.json
```

文件内容示例：

```json
{
  "a_token": "你的a-token",
  "xsrf_token": "你的x-xsrf-token",
  "cookie": "你的完整cookie",
  "bx_version": "2.5.36"
}
```

当前行为：

- 队列行里有 `operator_union_id` 时，worker 先找这个文件
- 找到就用该操作员会话上传 DingTalk
- 找不到才回退到全局 `DINGTALK_DOCS_A_TOKEN` / `DINGTALK_DOCS_XSRF_TOKEN` / `DINGTALK_DOCS_COOKIE`
- 队列行里没有 `operator_union_id` 时，直接使用全局会话
- `DingTalk_session_key` 和 `钉钉会话键` 也可以作为同一列用途的别名；最终都会映射到同一个 `<key>.json`
- 如果你在 Feishu `Document_link` 行里填的是 `alice`，那这里就必须准备 `alice.json`
- 共享 worker 如果打算按行切换 DingTalk 会话，建议把 `operator_union_id` 或它的别名当成启用 DingTalk 行的必填列；否则就统一走一套全局 `DINGTALK_DOCS_*`
- 当前队列已经会在 build 前先检查这个会话来源；缺少匹配的 `<key>.json` 且也没有全局会话时，会直接失败并把原因写回 `构建结果`

## 8. 怎样启用 DingTalk 同步

现在仓库已经支持一键启用 Feishu 主上传 + DingTalk 同步。

### 8.1 Feishu 上传

```powershell
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue_feishu.ps1 --dry-run
```

### 8.2 Feishu 主上传 + DingTalk 同步

```powershell
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue_dingtalk.ps1 --dry-run
```

### 8.3 跑单条记录

```powershell
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue_dingtalk.ps1 --record-id recvg0UCyT4IxR
```

### 8.4 公共包装器

如果你想继续用公共入口，也可以：

```powershell
$env:AUTO_MANUAL_ARTIFACT_SINK_PROVIDER='lark_drive'
$env:AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER='dingtalk_alidocs_session'
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue.ps1 --dry-run
```

但日常更推荐直接用：

- [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1)
- [`../scripts/process_build_queue_dingtalk.ps1`](../scripts/process_build_queue_dingtalk.ps1)

## 9. 队列行为不会变的部分

启用 DingTalk 同步后，这些行为保持不变：

- 仍然先从 Feishu `Document_link` 读待构建任务
- 仍然会先做 `sync-data`
- 仍然按 `Build_family` / `Git_ref` 走现有队列逻辑
- 仍然回写 Feishu 的：
  - `开始构建时间`
  - `构建结果`
  - `Document directory`
  - `Document link`

变化的是：

- `Document link` 继续保持 Feishu/wiki 主链接
- 如果表里有 `Document link_dd`，并且这行启用了 DingTalk 同步，队列会把 DingTalk 节点链接写到这个补充字段
- 如果表里没有 `是否上传钉钉`，worker 会按当前全局模式处理整行：开启 mirror 的 worker 会同步 DingTalk，Feishu-only worker 不会同步

## 10. 上传成功后你会看到什么

上传成功后，`commit` 响应里会返回新文件节点信息，典型字段包括：

- `dentryUuid`
- `name`
- `parentDentryUuid`

代码会把它转换成：

```text
https://alidocs.dingtalk.com/i/nodes/<dentryUuid>
```

然后把这个链接回写到 Feishu `Document link_dd`。

## 11. 什么时候需要重新抓值

这套方案是“浏览器会话上传”。
所以以下情况后，变量可能失效：

- 你重新登录了 DingTalk 网页
- 浏览器会话过期
- 钉钉强制刷新 token
- Cookie 被清掉

常见表现：

- 上传时报 401 / 403
- `uploadinfo` 失败
- `commit` 失败
- 目录明明存在，但上传立刻被拒绝

这时的处理方式不是改代码，而是：

1. 重新打开目标目录页面
2. 再抓一次新的 `uploadinfo` 或 `commit`
3. 更新这几个环境变量

## 12. 安全建议

这几个值都属于高敏感浏览器会话信息。

不要：

- 提交到仓库
- 写进 `.env` 并提交
- 发到群里
- 放到长期公开脚本里

建议：

- 只写到本机用户环境变量
- 或只在当前终端临时导出
- 如果你怀疑泄露，立即重新登录 DingTalk，让旧会话失效

## 13. 最常见的配置错误

### 13.1 只复制了一个 cookie

错误做法：

- 只复制 `XSRF-TOKEN=...`

正确做法：

- 复制请求头里的整段 `cookie` header

### 13.2 把单个文档 URL 当成目标目录

错误做法：

- 用已经上传好的某个文件节点作为 `DINGTALK_DOCS_TARGET_NODE_URL`

正确做法：

- 用你真正想作为上传落点的“目录页面 URL”

### 13.3 在旧 PowerShell 里看不到用户环境变量

写完用户环境变量后，旧窗口不会自动刷新。

正确做法：

1. 关掉当前 PowerShell
2. 新开一个 PowerShell
3. 再执行脚本

### 13.4 DingTalk 变量配了，但 Feishu 变量没配

这个模式不是“完全脱离 Feishu”。
当前队列控制面和回写表仍然在 Feishu。

所以这些 Feishu 变量还是要有：

- `FEISHU_PHASE2_BASE_TOKEN`
- `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID`
- `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`

## 14. 推荐的本地使用顺序

第一次配置：

1. 在 DingTalk 页面抓到 `a-token`、`x-xsrf-token`、`cookie`
2. 写入 `DINGTALK_DOCS_*` 用户环境变量
3. 新开 PowerShell
4. 执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue_dingtalk.ps1 --dry-run
```

通过后，再跑真实记录：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\process_build_queue_dingtalk.ps1 --record-id <你的record_id>
```

日常切换：

- 要传 Feishu：用 [`../scripts/process_build_queue_feishu.ps1`](../scripts/process_build_queue_feishu.ps1)
- 要传 DingTalk：用 [`../scripts/process_build_queue_dingtalk.ps1`](../scripts/process_build_queue_dingtalk.ps1)

## 15. 当前已知边界

当前这条 DingTalk 上传路径：

- 已验证可用
- 已接入 `process-build-queue`
- 已支持把 DingTalk 节点链接回写到 Feishu

但它仍然是浏览器会话模式。
所以它更适合：

- 本地操作员机器
- 有人值守的桌面环境

不适合直接当成：

- 长期稳定的公开 OpenAPI 集成
- 无浏览器会话的远程 GitHub Actions 默认方案

如果你想让 GitHub Actions 也支持可选 DingTalk mirror，现在可以额外配置：

- GitHub Secrets：
  - `DINGTALK_DOCS_A_TOKEN`
  - `DINGTALK_DOCS_XSRF_TOKEN`
  - `DINGTALK_DOCS_COOKIE`
- GitHub Actions repository variable：
  - `AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER=dingtalk_alidocs_session`

不配置这个 repository variable 时，远端 worker 仍然默认只保留 Feishu 主上传。

如果未来 DingTalk 给出正式开放接口，这份指南再切换到更稳定的文档化方案。
