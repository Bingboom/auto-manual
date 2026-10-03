# 工作台数据持续更新

Status: active

## 接入调查与实现计划

现有 `rtd_deliverables.py export` 与 `rtd_system_workspace.py corpus-export`
直接覆盖工程快照；分页缺少响应完整性和重复页检查。队列批次入口是
`tools/build_queue/orchestration.py`，单组成功写回在 `tools/build_queue/group_processing.py`。
现有业务内容保护范围是 `docs/publish` 和 `docs/knowledge`；工程同步会覆盖
其他目录。RTD 已提供 `manual-deployment.json` 页面字节哈希回执。

本批先接通 Word／印刷包的完成写回，再复用到语料批次和手动补刷。

1. 共用严格分页读取和快照安全写入；校验候选与上次有效值，失败保留原文件。
2. 按成功批次输出刷新请求；失败、取消、dry run 不触发。刷新失败独立于生产结果。
3. 在已有 bot 环境读取数据，候选写入 `docs/knowledge/workspace-data`，通过内容 PR 审核。
4. 页面优先读取业务快照，兼容迁移前工程快照；显示独立日期、状态和标识。
5. 合入后的独立验证检查目标 commit、来源哈希与线上页面字节；失败可单独重跑。

不新增事件推断、实时浏览器飞书查询、定时轮询、分析平台或全量说明书构建。
不自动合入或修改源表。工作流修改需 AGENTS.md §8.7 单独批准。

## 验证计划

用确定性 fixtures 覆盖交付成功写回、批次去重、空集、分页中断、重复页、
身份不匹配、异常减少、原子写失败、无变化和发布版本不匹配。
通过现有页面渲染测试验证刚构建但过期的业务数据仍为待更新。
仅执行本需求影响的测试集合及代码、文档门禁，不为刷新重新生产说明书。
真实源表交付和最终发布验收必须另有实际证据，不以 fixtures 替代。

## 日常入口与补做

Word／印刷包：Hello-Docs 的 **Feishu Build Queue** 与 **Feishu Draft Build Queue** 在批次交付链接写回并读回一致后，
每批导出一次。失败组不计入请求；成功组已完成的交付不因快照失败被改为未交付。
`.tmp/workspace-refresh/request.json` 记录批次身份；执行日志与 artifact 保存尝试、
检查时间、快照哈希和内容 PR 链接。来源无变化不制造时间戳提交。

语料：现有 `revision-ledger tm-apply`／云文档 TM 写回在整批写入并 GET 验证后
可输出同样请求。已授权的本机批次用以下包装器启动，原命令和审批参数保持原样：

```bash
python -m tools.workspace_refresh_batch corpus -- python -m tools.revision_ledger tm-apply ...
```

`...` 替换为原有已获批准的参数；包装器不授予源表写入权限。失败或 dry run 没有
完成请求，不刷新。该包装器默认使用 `lark-cli --profile prod` 的 bot。
其他入库工具尚无完成回执时，批次负责人在完成后使用下面的统一补刷入口。

打开 Hello-Docs **Actions → Workspace Data Refresh → Run workflow**，
选择 `deliverables`（交付）或 `corpus`（语料）。它只刷新对应来源，不重建说明书。
导出失败保留旧值并提交可审核的失败状态；同一事件仅一个 GitHub issue，不重复评论。
已有内容 PR 会被复用，不自动合入。审核人员检查来源、减少保护和执行记录后合入。

| 卡住的阶段 | 操作者补做 |
| --- | --- |
| 源表交付写回／读回失败 | 按原生产日志修复对应记录；确认链接可读后运行 Workspace Data Refresh |
| 导出、分页或校验失败 | 查看 workspace-refresh artifact；确认源表或权限后重新运行 Workspace Data Refresh |
| 内容 PR 提交失败 | 重跑补刷任务；幂等比较避免重复提交，不重跑生产 |
| 内容 PR 待审核 | 打开日志中的 PR，按现有审核流程处理 |
| 工程镜像同步失败 | 在 auto-manual 重跑 Sync Hello-Docs Mirror |
| RTD 构建失败 | 在 RTD 重试目标版本的构建 |
| 线上版本／快照不一致 | 在 Hello-Docs 手动运行 Workspace Data Verify；只查版本与哈希 |

来源绑定采用 `workspace_refresh_sources.json` 中的身份哈希，基于双平面地图的
业务构建表与唯一 TM-B；不记录凭据。只读导出仍复用 `rtd_deliverables.export_snapshot`
和 `rtd_system_workspace.corpus_export`。语料仅保存汇总、状态计数和源内容哈希；
同条数文本修订也会改变内容标识，不公开语料正文。

## 存储、确认时间与发布

- `docs/knowledge/workspace-data` 是 Hello-Docs 审核后的业务冻结数据，沿用既有内容保护；
  不向工程仓库提交该目录，不从业务仓库反向改工程代码。
- 该目录不存在对应快照时，兼容 `tools/rtd_portal_assets` 的迁移前基线；
  业务快照存在但损坏时显示 Unavailable，不能静默退回工程旧数字。
- 首次导出允许结构完整的空集；已有有效数据减少时停止替换，要求核查来源，
  不把读取失败或失联目标当成合法删除。人工确认的真实删除应另开范围明确的快照内容 PR，
  通过同样审核更新基线后恢复自动刷新。
- 页面显示构建时间、交付快照日期、语料快照日期与内容 SHA256。
  新鲜度阈值集中在 `source_registry.yaml`：交付 3 天、语料 7 天。
- 无内容变化的成功检查只记录在执行日志；冻结快照仍保留上次内容日期，
  页面过期提示不会因一次新的页面构建或未发布的检查记录消失。
  该提示表示需要确认，并非数据必然错误；近期无变化检查可从更新记录查证。
- 工程代码先经过审核、合入、镜像同步；之后业务数据内容 PR 直接进入 Hello-Docs main，
  不需要把业务数据再送回工程面。正常 RTD 构建继续消费冻结文件。
- 部署回执新增 `workspace_revision`、两类快照及状态文件哈希。
  Workspace Data Verify 检查 mainline 身份、目标 RTD 构建成功、线上回执版本、快照哈希、
  页面字节及页面引用的快照哈希。未完成最后一步不能称为“工作台已更新”。
- 线上核验只在相关 main 合入或人工补做时触发，最多 20 次、间隔 30 秒等待目标构建，
  没有 schedule，不轮询飞书，不重建说明书。失败记录最后到达阶段，可单独补做。
- 已发布的失败状态仍然显示旧数字；任务日志先立即反映刷新失败，静态页面的失败状态
  要随内容 PR 审核发布。审核等待期间不宣称页面已经知道最新任务状态。

7/30 天活动、人工介入率和回流后再采用仍为 Not tracked yet；快照差、Git 次数和文件时间
不产生业务事件。候选分支为每个来源一个，非快照路径会在 push 前被拒绝。

## 本批验证记录

- 本地测试涵盖完整分页、断页、重复页、空集、结构变化、异常减少、原子替换失败、
  内容无变化、语料等量修订、读回触发、重复批次、时间戳去重和线上版本／字节不匹配。
- 2026-10-03 UTC：使用 prod bot 只读试导出真实交付表，得到 `unchanged`；
  候选与日志只留在工作树 `.tmp/workspace-refresh-pilot`，未写源表、未提交业务快照。
- 工作流修改获操作者明确批准（2026-10-02：“授权按该范围修改工作流”）。
  不含自动合入授权。真实新增交付的自动触发与 RTD 最终验收须在工程 PR 审核发布后进行，
  不以本地 fixtures 或试导出代替线上生产验收。

- 2026-10-03 UTC：真实 TM-B 完整分页试导出通过，返回 `changed`；候选仅在 `.tmp`，未发布业务数据。

- 首次部署核验发现：共用部署下载器拒绝查询参数，RTD 构建列表必须使用无查询的默认分页 URL。已补跨真实下载器 URL 闸门的回归测试；故障日志正确停在 rtd-build，未误报已更新。
