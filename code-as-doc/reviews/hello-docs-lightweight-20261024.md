# Hello-Docs 轻量化：当前审计、P0 实施与后续门禁

Status: active

审计日期：2026-10-24（America/Los_Angeles）。本记录先于 P0 代码修改建立。
依据为三个仓库当前 main、完整 workflow 文件与 Actions REST API，非需求中的名称推断。
[聚合证据](hello-docs-lightweight-20261024.json)只含配置和运行统计，不含业务正文或凭据。
定位依据：[项目定位 §1、§5](../architecture/Hello_Docs_Positioning.md)、[双平面地图](../../user-guide/two_plane_map.md)。

## 1. 当前事实与职责

- auto-manual main `f2aa10398dc6acc5dc50a2b12931c1276059d2cf`，公开、Actions 开启。
- Hello-Docs main `61d460127fb610259d4932ef0994d4ec9da92444`，公开、Actions 开启。
- Review 的 main SHA 见聚合证据；私有、Actions **关闭**。18 份工作流与工程面逐字节一致，
  5 条运行记录全部是 Dependabot dynamic 更新；无重复工程 CI 运行的证据。启用 Actions 后旧定义有重复执行风险。
- 三仓均有 18 份工作流。`manual-validation.yml` 有 17 个 job，缺少 repo 守卫；
  Nightly、Review Preview、Manifest Diff 同样缺少守卫。Review Preview 使用 fixture、`--all-review-models --skip-word`，
  是工程 smoke，不是 `docs/review-drafts` 私有 RTD 站部署。
- auto-manual main 有 active ruleset；传统 branch protection API 返回 404。active ruleset 要求的 16 个状态名称与原来相同，均保留；`node-ui` 仍是附加工程检查。
  Hello-Docs 无 ruleset/传统保护；Review 的保护 API 返回套餐限制 403，不能断言有保护。
  本 PR 不改保护。以后启用 required checks 前必须核对业务侧新检查名称。CI 范围校验不是服务器端权限或分支保护；工作流修改本身仍需人工审核。

| 工作流 | 当前触发 | 定义 job 数 | 分类与 P0 处置 |
| --- | --- | ---: | --- |
| `backport-reminder.yml` | schedule, workflow_dispatch | 1 | 保留：工程/业务回收哨兵，各自凭据 |
| `cred-health-check.yml` | schedule, workflow_dispatch | 1 | 保留：凭据与权限健康检查 |
| `feishu-build-queue.yml` | workflow_dispatch | 1 | 保留按需；P1 候选：多格式重构建 |
| `feishu-draft-build-queue.yml` | workflow_dispatch | 1 | 保留按需；P1 候选：初稿构建 |
| `feishu-schema-parity.yml` | schedule, workflow_dispatch | 1 | 保留：仅工程面 schema 哨兵 |
| `feishu-start-review.yml` | workflow_dispatch | 1 | 保留：评审初始化与状态回写 |
| `feishu-web-publish-queue.yml` | workflow_dispatch | 1 | 保留：业务 Web Publish、范围门禁、发布 PR |
| `manifest-regenerate-diff.yml` | pull_request, workflow_dispatch | 1 | 工程配置再生成：仅 auto-manual |
| `manual-validation.yml` | push, pull_request | 17 | 拆分：16 工程 job 仅工程面；保留 secret-scan，新增 business-content |
| `nightly-render.yml` | schedule, workflow_dispatch | 1 | 工程 smoke：仅 auto-manual |
| `phase2-content-backup.yml` | schedule, workflow_dispatch | 1 | 保留：Hello-Docs 业务源与 TM-B 90 天备份 |
| `review-branch-sync-check.yml` | schedule, workflow_dispatch | 1 | 保留：仅工程面 review 分支漂移哨兵 |
| `review-preview.yml` | pull_request, workflow_dispatch | 1 | fixture smoke 包装：仅 auto-manual；非私有审核站部署 |
| `sync-hello-docs.yml` | push, workflow_dispatch | 2 | 保留：两个单向工程同步与失败通知 |
| `verify-web-deployment.yml` | schedule, workflow_dispatch | 1 | 保留：每日/手动线上发布资源校验 |
| `web-publish-receipt.yml` | push, workflow_dispatch | 1 | 保留：部署验证后回写、同记录回读 |
| `workspace-data-refresh.yml` | schedule, workflow_dispatch | 1 | 保留：业务快照读取、内容 PR、失败保留旧数据 |
| `workspace-data-verify.yml` | push, workflow_dispatch | 1 | 保留：main/RTD/线上源 hash 校验 |

## 2. 镜像、依赖与不变量

`sync-hello-docs.yml` → `scripts/sync_mirror.sh`：以源工程树组合镜像拥有的子树，提交以镜像当前
HEAD 为父，普通 push；远端并发推进会拒绝覆盖。Hello-Docs 保留 `docs/publish`、`docs/knowledge`，
Review 保留 `docs/review-drafts`；源树出现三者中任一目录都会失败。各仓 README 从工程面的
`mirrors/<repo>/README.md` 安装。P0 不改变这些参数、对象组合和 push 机制；不从私有仓取内容到公开工程面。

业务依赖链：

1. Feishu/OpenClaw dispatch → 按需队列 → 自有隔离快照/构建 → 状态回写或发布候选 PR。
2. Web Publish → Hello-Docs `docs/publish/**` PR → main → 外部 RTD 构建 →
   receipt 校验部署指纹、页面/资源 → `HTML_link` 幂等回写并回读。失败/超时不能登记成功。
3. Workspace 读取来源 → 内容 PR → main 镜像保持 → RTD → Workspace Verify；失败保持旧快照。
4. Phase2/TM-B 每晚备份 → 90 天 artifact → 失败哨兵；schema parity 在工程面独立运行。
5. Review 私有 RTD 根据 Git 内容构建审核站；不依赖 GitHub Review Preview smoke。

上列工作流的触发、暂停变量、权限、secrets 引用、状态机、备份保留期和部署验证命令均保持原样。
工程 CI 仍使用 fixtures，不向真实飞书源表写数据。数据业务语义、SSOT、格式生成器均不改。
镜像依赖工程面受保护 PR 的验证；现有 Sync 不等待 main 推送后的 Manual Validation，
P0 不改变这一时序。main 后续验证失败时应修复/回滚工程面再同步，不能绕过发布回执。

## 3. 成本基线与估算方法

这是每仓最新一页（最多 100 条）运行的**有界样本**，不是完整日/月账单，也不跨仓比较运行频率。
API 采集在同一次审计内完成，run/job 状态可能继续变化；只统计有完成时间且非 skipped 的 job。

| 仓库/工作流 | 样本运行数 | 已完成 job 数 | 实际 job 分钟 | 逐 job 向上取整分钟 |
| --- | ---: | ---: | ---: | ---: |
| Hello-Docs Manual Validation | 29 | 476 | 1342.53 | 1594 |
| Hello-Docs Nightly Render | 4 | 4 | 19.15 | 21 |
| auto-manual Manual Validation | 44 | 747 | 1880.82 | 2186 |
| auto-manual Review Preview | 27 | 27 | 88.15 | 99 |
| auto-manual Nightly Render | 2 | 2 | 6.38 | 8 |

Hello-Docs 样本：2026-10-21T11:36:18Z 至 2026-10-25T01:06:41Z；auto-manual：
2026-10-23T06:56:33Z 至 2026-10-25T02:08:27Z。Review 仅 5 条 dynamic 记录。
Hello-Docs Manual Validation 取整分钟中：unit 573、check-all 182、doctor-en 160、secret-scan 59。
业务 Repo 当前公开，标准 hosted runner CI 不应把这些分钟直接当成现有私有仓账单。

反事实估算：同样事件和 runner 下，删去的 16 个工程 job + Nightly 共约
`1594 - 59 + 21 = 1556` 个取整 runner 分钟；再扣新增 business-content 的实际分钟。
若每次 business-content 为 1–2 个计费分钟，29 次共 29–58，则样本净减约 1498–1527 分钟，
相对这两条工作流的 1615 分钟约 92.8%–94.6%。这是待实测的假设，非已实现节省。
全仓这个 100-run 样本合计 1884 个取整代理分钟，含保留的业务任务 269 分钟；
按同一假设，P0 对全样本的净减约为 79.5%–81.1%，剩余约 357–386 分钟。
这也不是月账单预测，且不含样本没有发生的按需构建。
当前 Hello-Docs 样本未运行 Review Preview/Manifest Diff，不能替它们虚构历史节省；Review 关闭 Actions，当前节省为零。

复算公式：`sum(max(0, completed_at-started_at)/60)` 为 job 分钟；
`sum(ceil(seconds/60))` 为取整 proxy。API 的 duration 不是 GitHub 账单真值：免费额度、套餐、
取消 job、未启动失败、runner 类型与平台系数、存储/缓存/下载都影响金额。不得用整条 workflow 的墙钟时间代替并行 job 之和。
RTD 构建和私有托管按 RTD 自己的计划、构建额度及访问策略计费，不计入 Actions；P0 不减少或验证其账单。
另读取了样本中 3 次 Phase2/TM-B 备份的 artifact 元数据：压缩归档各约 0.80 MiB，均未过期，
有效期保持 90 天；未下载业务备份正文，也未把“artifact 存在”当成恢复演练通过。
P0 不承诺私有化后零费用，保留的业务核验、按需构建与存储仍须单独预算。

复采（需 GitHub 读取权限；完整月度报告须分页，jobs 也须分页，并按 run_attempt 去重）：

```sh
gh api 'repos/Bingboom/Hello-Docs/actions/runs?per_page=100'
gh api 'repos/Bingboom/Hello-Docs/actions/runs/RUN_ID/jobs?per_page=100'
gh api repos/Bingboom/Hello-Docs/actions/permissions
gh api repos/Bingboom/Hello-Docs/rulesets
```

实施后使用相同长度、相同事件类别的窗口，记录 content-check 和 secret-scan 实测值；
确认镜像/业务更新只分配两个 job，工程任务为 skipped。不要为取样触发生产队列或回执写入。

业务成本也须保留在基线中：同一 Hello-Docs 样本的 Workspace Verify 为 115 个取整分钟，
Receipt 64、Web Verify 40、Workspace Refresh 16、Phase2/TM-B Backup 15、凭据检查 13、
Backport Reminder 6。P0 对这些分钟不预报节省；耗时或失败均不能成为停用业务任务的理由。
本样本没有队列 dispatch，不能推断按需多格式构建没有成本。

## 4. 风险、P0 实施计划与验证安全网

- 修改 `manual-validation.yml`：16 个工程 job 加 exact repository 守卫，保留不带 repo 守卫的 secret-scan；
  新增只有两个命名镜像运行的 `business-content`，`contents: read`，不接 secrets、不安装渲染依赖；浅层稀疏 checkout 仅检出内容和脚本，按需取 base commit。
- Nightly、Review Preview、Manifest Diff 的唯一 job 加相同工程面守卫。触发定义保持不变，
  因而仍可出现 skipped workflow 记录；守卫在分配 runner 前评估，不用 `[skip ci]` 绕过安全检查。
- 新增 stdlib 内容检查脚本：PR 范围门禁、JSON/CSV 解析、发布清单结构与文件完整性。
  内容 PR 不能更改工程树；`review/*` 基线的 backport 仍允许 `docs/_review/**`。
- 守卫通过单向同步抵达镜像；不在镜像手改工作流，避免下次覆盖。同步后首次新事件才受新定义约束；
  已排队和历史 job 不会被本 PR 自动取消。
- 安全网：workflow 路由契约测试、真实本地 Git 镜像组合测试（两个镜像）、内容破损/越界/路径逃逸失败测试、
  Ruff → targeted unittest → full unittest → maintainability → doc links → fixture build check。
- 内容脚本不等价于业务审核、在线部署或浏览器验收。RTD 验证失败仍然红，不会因为减负变成成功。

既有失败（P0 前）：[Workspace Verify](https://github.com/Bingboom/Hello-Docs/actions/runs/39932695701)
失败于 current main deployment/source hashes；[Receipt](https://github.com/Bingboom/Hello-Docs/actions/runs/39977725732)
失败于 verify/register；[Web Verify](https://github.com/Bingboom/Hello-Docs/actions/runs/40076523495)
失败于 target verification；[Nightly](https://github.com/Bingboom/Hello-Docs/actions/runs/40095949606)
失败于 doctors/IDML pilot。本次只确认失败步骤，不推断原因。保留业务失败信号，单独跟进，不能声称当前生产链路全绿。
样本另有 3 次 Manual Validation 失败于 unit/maintainability，1 次 action_required 没有分配 job；
这些记录不等价于计费故障。所有计入分钟数的 job 都有已分配 runner ID。

## 5. 回滚与上线后验收

1. 由维护者审核、合入 auto-manual PR（本任务不自行合并）。记录合入 SHA 与两个镜像 sync run。
2. 读回两个镜像 workflow 守卫；核对所有权子树 tree OID 与同步前相同（期间合法业务更新须单独解释）。
3. 用普通内容 PR 验证 secret-scan/business-content；不为测试造生产发布。
   观察既有 Workspace/备份/队列按原计划执行；发布上线、回执、浏览器验收分别记录。
4. 回滚：在 auto-manual 新建 revert PR，恢复这四个工作流、删除新增 business-content job/脚本/测试，
   合入后由原 sync 同步。保留业务目录和所有既有历史；不要回退整个镜像 main。
5. 若内容门禁误报，先修复检测逻辑的 PR；紧急时回滚此 P0 PR，临时承担原工程 CI 费用。
   不关闭队列、备份、回执、扫描或 RTD。若 required checks 后来改变，先匹配名称再回滚，避免 PR 卡死。

## 6. P1：按需独立执行器（方案，未实现/未迁移）

优先使用现有 Mac mini/OpenClaw 的受控本地命令，不在本轮部署常驻 runner 或新平台。
第一批仅评估人工指定的 Word/PDF/IDML 构建：输入合同固定仓库+commit、冻结快照 hash、
目标型号/市场/语言/格式、授权和幂等任务 ID；隔离工作目录，锁定工具版本，禁止拉取任意 PR 后带生产凭据执行。
输出包括 artifact/hash、工具版本、输入指纹、日志、退出码、验收结果；经原有范围门禁接收为 PR。
失败保持上次有效交付；断电/超时不能推进正式状态。构建成功与 RTD 发布成功是两个状态。
最初通过人工接收结果保持单一写路径；并行期不得由 Actions 和本地执行器同时消费同一队列。
回滚为原 workflow_dispatch 路径，不删除原 worker。具备去重、锁、权限隔离、恢复演练及操作者批准后再迁移。
Mac mini 的维护、电力、凭据、容量、离线故障成本需和 hosted runner 分钟共同评估。

## 7. P2：私有化准备（清单，未执行）

- 导出实际计划/用量/账单，明确 Actions included minutes、artifact 90 天备份与缓存存储额度；设预算与报警。
- 检查 PAT/GitHub App 对两镜像 contents/workflows 的权限、到期与跨仓访问；只审计 secret 名称，不导出值。
- 在测试私有 Repo 验证 RTD 私有 Git 拉取、webhook、计划/付费、外部访问与私有内容隔离。
  Git 仓库 private 不会自动令已发布站点 private；正式外部阅读策略要单独决定。
- 核对 OpenClaw/本机/执行器 clone、dispatch、PR、API、artifact 下载；不通过公开仓库中转业务内容。
- Review 如需开启 Actions，先另行检查业务任务的现有 repo 守卫和凭据范围：部分队列/健康/提醒守卫
  并未排除 Review。本次只收敛工程任务，不替操作者启用 Actions 或重新配置这些业务任务。
- 检查所有自动化依赖匿名 raw/API URL、外部 badge/链接、发布者权限、required checks 与许可证策略。
- 备份完整 Git refs、业务子树 OID 与可恢复的 Phase2/TM-B artifact；演练受控恢复，失败不覆盖旧数据。
- 清理凭据泄漏需独立授权；转私有不会抹除公开历史/缓存。敏感扫描继续开启。
- 操作者明确批准后才切换 visibility；分开记录 Git 私有化、RTD 拉取、站点访问、备份、队列与回执验收。
- 切换失败时优先恢复访问/集成。重新设为 public 可能公开新增业务内容，**须另行批准**；
  不能自动把业务仓改回 public 作为无风险回滚。


## 8. 提交前复核

初始审计以后，工程 main 合入了韩国源包，推进到
`269a7c48dba3134bd3896e20583ee5c0b6939fbf`；本分支已基于该提交重放。
它没有修改 `.github/workflows`。两个镜像的当前 main 与 Actions 设置已再次读取，
18 份工作流的 Git blob ID 均与初始审计相同，详见聚合证据的 `submission_checkpoint`。
Review Actions 仍关闭；Hello-Docs 仍公开、Actions 开启。
成本统计保留初始采样窗口和 run ID，不把新的工程源包合入当成 P0 已上线或已节省费用。

本地校验环境曾因稀疏输入和 CSV checkout 格式而失败；已核验补齐 Git 对象，并恢复
Git 属性要求的 checkout 字节。没有修改已跟踪源文件的 Git 内容、冻结哈希或测试基线；业务 CSV 没有提交差异。
验证命令与最终结果见本节后续记录和 PR。


### 最终本地验证

- `TMPDIR=/private/tmp python3 -m unittest -v`：5672 tests，67 skipped，0 failures/errors（2996.854s）。
  基于 `269a7c48` 的完整检出执行；此前 checkout 格式问题已修复，相关单例重跑通过。
- 65 项定向 workflow/内容/真实 Git 镜像组合用例通过（完整单测也包含这批用例）；其中 15 项是新增门禁回归。
- Ruff、文档链接/生命周期、maintainability 均通过；冻结包没有新增 drift，两个镜像的拥有目录没有交叉。
- `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2` 通过。
- 14 份非目标 workflow 逐字节保持一致，原 17 个 Manual Validation job 的 steps 均保持一致；新 shell 已通过 `bash -n`。
- 本地 env preflight 提示 1 个缺失依赖和 20 个版本与 lock 不同；未更改依赖文件。远端锁定环境 CI 与上述本地结果分开记录。
- 未 dispatch 生产队列、Workspace、备份或回执；没有实时 Feishu、RTD 发布/私有化或浏览器验收。

本 PR 合入和镜像同步之前，P0 尚未在业务仓运行；成本减少仍为条件估算。


### 最后集成基线

完整单测通过后，main 再推进到 `32b6a45941a0cdffb67b55fc8782dfa9f073d680`
（工作台 issue register / draft checks / review-table sync，#1604）。本分支保留该更新；
它没有改动本 PR 的 workflow 或内容检查脚本。完整单测结果对应 `269a7c48` + P0 代码；
最后基线以相关 Review 模块和 P0 门禁集成复核，远端 CI 另按最终 head 执行。


最后集成复核：`TMPDIR=/private/tmp python3 -m unittest` 加上述 10 个 workflow/内容测试模块，
以及 `tests.test_rtd_review_site tests.test_rtd_review_table_sync`，合计 **91 tests，0 failures/errors**。
最终 Ruff、结构门禁和文档检查再次通过。与完整单测通过时相比，P0 的 4 份 workflow、
检查脚本及其回归测试的 Git blob 均一致；最后变动是上游集成与审计文档。
