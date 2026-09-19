# 说明书产线盘活执行台账

状态：规划登记，尚未启动实施。关联 [方案 v3.1](../manual_production_revitalization_plan.md)、
[执行优先级](../optimization_project.md)及 [PR #1188](https://github.com/Bingboom/auto-manual/pull/1188)。

本文件是本轮 34 项任务的唯一执行状态入口。方案保留范围，路线图保留方向和优先级，
PR/报告保存证据；不在多份文件分别勾选同一任务。既有 OPS 能力不因此重新变成未交付，
下面记录的是本轮核对、整合和扩展任务。

## 1. 执行规则

1. **防漏项**：方案每项对应唯一 REV-ID；新增、拆分、取消保留原 ID 和变更理由，禁止删行掩盖未完成项。
   拆分使用 REV-xx-a 等子 ID，父项必须等全部必要子项验收。Issue/PR 可以链接本台账，但不复制状态主表。
2. **防抢跑**：开工前从最新主线读取本台账、相关源记录和已开 PR；有 active/verifying 项先续接。
   没有进行中项时，选择依赖满足且优先级最靠前的 planned 项。前置项须为 done；阶段门须有验收记录。
   时间到了不能替代依赖通过。已有授权持续有效；仅缺失的具体生产操作授权需要补齐。
3. **防分散**：默认一个主要 active 切片；只有相互独立、范围明确时才由操作者决定并行。
   开工记录执行人、目标/语言/版本、允许修改面、不做范围、交付物、验收方式、回退方式和关联 PR。
   未指定目标、执行人或验收条件，不进入 active，不用泛化任务填补空缺。
   执行代理可在已授权范围内登记自己负责的切片，不为登记负责人重复询问已确认事项。
4. **防假完成**：planned → active → verifying → done。verifying 表示已有产物待验收；done 必须
   同时有可访问证据、验收结论/验收人/日期，实施 PR 须记录实际合入状态。
   涉及发布还须提供实际部署版本/线上验证；在线写入须同记录回读。代码合入或 CI 绿不能代替这些证据。
5. **防失联**：blocked 必填阻塞点、解锁责任人、下一动作和复查日期或外部事件；deferred 必填理由及重启条件。
   cancelled 须有操作者范围决定及影响记录，不能算完成。不得默默跳过阻塞项，也不把无触发条件的长期项强行开工。
6. **防跑偏**：每个实施 PR 标明 REV-ID，并按方案范围和验收结果复核。
   新需求先记到范围变更表，说明来源、收益、代价及依赖影响，获范围决定后再改任务。
   顺手重构、恢复已撤回产线、添加无实际消费者的平台能力不能混入当前切片。
7. **可续接**：每轮结束前更新本表及第 4 节续接记录，写清做到哪、证据在哪、剩余什么、下一项是什么。
   下一执行者以主线和在审 PR 的实际状态核对后续接，不只依赖聊天记忆；同一项已有 PR 时先检查它，避免重复建设。

本台账是执行与评审约束，**当前不是自动调度器，也没有新增强制 CI 门禁**。
它能提供逐项核对依据，不能保证无人触发时自动执行。实际每轮执行人负责回写，发布/内容验收人负责结果判断。
如果后续要定期唤醒或自动检查，应另行明确运行环境、节奏、权限和通知条件，再实施；本文不声明这些已经启用。

## 2. 任务登记

初始均未开工；“待指派 / —”不是可接受的 active/done 记录。
依赖列的 G1–G4 定义见第 3 节；外部授权、内容批准及原有架构门槛仍需同时满足。
状态和证据要在任务实施 PR 中同步更新；最终验收发生在合入或部署之后时，用后续台账更新记录真实结果，不能预先填 done。

| ID | 所属工作 | 前置依赖 | 退出证据 | 状态 | 执行人 / 验收与证据记录 |
|---|---|---|---|---|---|
| <a id="rev-01"></a>REV-01 | WP1 | — | 两站配置、部署提交、版本、旧新 URL 同时点清单；不以截图代替查询 | done | 执行=Claude（Fable）调查 2026-09-19；证据=[revitalization/rev01_inventory.md](revitalization/rev01_inventory.md)、[revitalization/rev01_url_map.csv](revitalization/rev01_url_map.csv)——两站构建号/分支绑定全部核实，旧站 HT-Manuals 事实冻结（仅建项构建、无 webhook、仅 JE-1000F US 1.7 一本），新站 52 目标全 200；RTD 后台仅登录可见项标待操作者确认。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-02"></a>REV-02 | WP1 | REV-01 | HTML_link、印刷二维码、交付链接原值及最新/历史语义对应表 | done | 执行=Claude（Fable）调查 2026-09-19；证据=[revitalization/rev02_link_audit.csv](revitalization/rev02_link_audit.csv)、[revitalization/rev02_conclusions.md](revitalization/rev02_conclusions.md)——构建表 33 行 HTML_link 零旧域名（3 非空全 ht-doc）、发布文档管理 45 链接全 alidocs、印刷 QR 全物料号非 URL：旧站下线暴露面为 0；发现 HTML_link 登记形态不一致（平铺别名 vs 嵌套正式，待 M2/M4 统一拍板）。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-03"></a>REV-03 | WP1 | REV-02, REV-06, REV-08 | 获批迁移范围、旧入口到 HT-Doc 的实际跳转/兼容配置与验证、旧站停止独立更新证据、映射恢复记录；保留历史版本语义及 publish 分支 | done | 执行=操作者删除旧站 + Claude（Fable）核验 2026-09-19；证据=[revitalization/rev03_closing.md](revitalization/rev03_closing.md)——四条死亡探针 404、新站回归全绿、旧链接由新站兼容页承接、publish 分支在位（未删）。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-04"></a>REV-04 | WP1 | REV-01 | 带时间/来源/维度的型号×区域×语言覆盖清单；解释 24/47/52 差异 | done | 执行=Claude（Fable）调查 2026-09-19；证据=[revitalization/rev04_coverage.csv](revitalization/rev04_coverage.csv)、[revitalization/rev04_explain.md](revitalization/rev04_explain.md)——24/47/52 全部闭环（47=运营表快照与 manifest@HD#82 集合级相等；52=撤两本 sideload 后现状=22 本；24=撤前峰值本数），运营表漂移 5 行（JE-1000H EU 非英语）；JE-1000H EU 已解、JE-3000C KR 部分解。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-05"></a>REV-05 | WP1 | — | 命令/调度/归档/同步能力矩阵，逐项标已有、缺口、待核实；不恢复撤回命令 | done | 执行=Claude（Fable）调查 2026-09-19；证据=[revitalization/rev05_capability_matrix.md](revitalization/rev05_capability_matrix.md)——34 动作/14 workflow 全录，撤回四命令双面证实不在 main；月报调度已核实=操作者本机 Claude 定时任务 monthly-manual-traffic-report（cron 0 9 1 * *，enabled，2026-10-01 首跑）；REV-08 缺口坐实（回执不校验目标项目、校验器无调用者、HTML_link 部署前回写）。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-06"></a>REV-06 | WP1 | REV-02, REV-04, REV-05 | M0 差异表；每个差异有解释、责任人和处理决定，不补造队列历史 | done | 执行=Claude（Fable）调查 2026-09-19；证据=[revitalization/rev06_m0_diff.md](revitalization/rev06_m0_diff.md)——12 条差异（8 已解释历史差异 / 2 必要+1 可选待授权写 / 3 待决策）；新发现：JE-2000F_EU 队列行为 FAILED 属正确行为但 49/52 目标无回执、JE-1000F_US_2.2 行仍武装有误重跑风险、reports/releases 在 git 为空集（by design）→ M1 唯一冻结记录=Hello-Docs manifest；撤下两书五面零残留。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-07"></a>REV-07 | WP2 | REV-06, REV-08 | M1/M2 缺口切片；幂等、登记失败独立重试、人工字段保护及授权回读证据 | verifying | 执行=Claude（Fable）2026-09-19 开工（操作者「继续 从REV-07开工」）；范围=M2 运营表幂等同步 + M1 三面持续核对（本 PR：`tools/ops_catalog_sync.py` sync/reconcile、白名单 `data/ops_catalog_reconcile_whitelist.json`、契约 `web_publish_pipeline.md` §2.3、21 项单测）+ 姊妹 PR（HTML_link 写回后移，另开切片）；不做=存量 49 回执补录（待操作者 M2 决策）、reconcile 定时化（归 REV-16）；产物与实跑证据=[revitalization/rev07_m2_log.md](revitalization/rev07_m2_log.md)——dry-run 存档→授权写 1 行（运营表 row20 JE-1000H/EU/en 机器列刷新，revision 27→28，行数 52 不变，回读人工列逐字未动）→幂等复跑 52 in_sync 零写→reconcile exit 0（known=49 全 M0-05 白名单命中，new=0）；回退=运营表该行按日志前值改回即可（单行、值全记录）；验收=本 PR 合入 + 操作者复核实跑日志 |
| <a id="rev-08"></a>REV-08 | WP2 | REV-05 | 两条路径的 RTD 项目/main 分支/发布 URL 一致性检查，正确站点通过及错误站点拒绝验收/登记的证据；区分批准、合入、部署、线上版本回执。已有能力复用，缺口实现另开切片 | done | 执行=Claude（Fable）实现 2026-09-19；产物=PR [#1190](https://github.com/Bingboom/auto-manual/pull/1190)/[#1192](https://github.com/Bingboom/auto-manual/pull/1192)（每日校验 cron 上线）+ 429 限流修复 [#1193](https://github.com/Bingboom/auto-manual/pull/1193)；**验收条件已全部满足**：#1193 已 squash 合入 main（`b0f60e53`）、合后全量校验绿跑（run [35451362215](https://github.com/Bingboom/auto-manual/actions/runs/35451362215) 成功）、哨兵 Hello-Docs#91 已关闭；操作者 2026-09-19 预验收原话「合并 验收」（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)） |
| <a id="rev-09"></a>REV-09 | WP2 | REV-07, REV-08 | 代表目标修订/发布/恢复证据；已有演练复用，新演练区分隔离环境和生产 | planned | 待指派 / — |
| <a id="rev-10"></a>REV-10 | WP2/WP3 | REV-02, REV-04, REV-05 | M4/M5 入口映射历史、统计窗口/过滤版本及目录快照；不覆盖旧统计 | done | 执行=Claude（Fable）草拟 2026-09-19；证据=[revitalization/rev10_entry_map.md](revitalization/rev10_entry_map.md)（M4 映射表 v1：52 根别名+22 兼容页+门户，历史变更栏立表）、[revitalization/rev10_metrics_snapshot.md](revitalization/rev10_metrics_snapshot.md)（M5 口径快照第一期：窗口/来源/过滤/归类/目录指针/命名 v1；未含 CWA 实测——凭据边界）。快照落盘路径约定待 M5 实施定。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-11"></a>REV-11 | WP3 | — | 真实候选清单及语言责任人审核；批准、拒绝、待定分开，授权入库须回读 | done | 执行=Claude（Fable）2026-09-19 完成首批全链；证据=[revitalization/tm_writes_20260919.md](revitalization/tm_writes_20260919.md)——74 行补 Draft、59 行转 Approved（7 行带改值）、81 条 ledger 盖章、tm-candidates 43→回灌写 2+幂等 2、AC/AC1 冲突经操作者裁决（按 2000E）落库并压制反向候选。剩余：116 需复核、372 留人工、37 未解析候选（建行需新授权）归月度批次。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-12"></a>REV-12 | WP1 | REV-04, REV-06 | 大陆访问实测范围、IT 待办及具体下一批目标；域名阻塞有负责人和恢复条件 | done | 执行=Claude（Fable）综合 2026-09-19；证据=[revitalization/rev12_reachability_and_next.md](revitalization/rev12_reachability_and_next.md)——大陆实测范围六项清单（待大陆侧执行）、IT 待办登记（DNS 阻塞责任人=IT，恢复条件=交接窗口）、下一批目标=中规 JE-2000F CN ≈ 日规 JE-1000F JP（韩规先修构建声明）。；**验收=夏冰 2026-09-19**（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)，原话「合并 验收」） |
| <a id="rev-13"></a>REV-13 | WP2 | G1 | 不同结构代表目标的发布证据及人工操作记录；不能只测同一本 | planned | 待指派 / — |
| <a id="rev-14"></a>REV-14 | WP2 | G1, REV-08 | M3 业务选择/冻结输入/能力声明映射与正反例；不机械要求异义字段相等 | planned | 待指派 / — |
| <a id="rev-15"></a>REV-15 | 维护扩展 | G1 | 共享组件影响目标、重建/回归/重审清单，落实源头和责任 | planned | 待指派 / — |
| <a id="rev-16"></a>REV-16 | WP3 | G1, REV-07, REV-10 | 运营目录/访问数据增量更新、人工字段保护、每期快照及失败处理证据 | planned | 待指派 / — |
| <a id="rev-17"></a>REV-17 | WP3 | REV-16 | 首轮月度复核记录，包含改进/调查/无需动作及判断理由 | planned | 待指派 / — |
| <a id="rev-18"></a>REV-18 | WP3 | REV-11 | 批准 TM 在真实预翻译中的命中/人工修正记录；无语言资源则保留阻塞 | planned | 待指派 / — |
| <a id="rev-19"></a>REV-19 | 区域试点 | G1, REV-12, REV-13 | 一个明确型号×区域×语言的来源、输出、审核、部署及访问验收 | planned | 待指派 / — |
| <a id="rev-20"></a>REV-20 | IDML 试点 | REV-04 | 代表产品族和原生 IDML 组件/分页/字体/溢出验收清单；独立于 Web 阶段门 | planned | 待指派 / — |
| <a id="rev-21"></a>REV-21 | 覆盖扩展 | G2, REV-22 | 具体扩展批次及每目标成本；大规模传播另须现有 Phase 2 / Workstream V 门槛 | planned | 待指派 / — |
| <a id="rev-22"></a>REV-22 | 维护指标 | G2 | 与首月同口径比较人工干预、周期、返工、恢复；缺失为 no_data，不伪造改善 | planned | 待指派 / — |
| <a id="rev-23"></a>REV-23 | 内容修复 | G2, REV-15 | 真实内容问题关联来源、修复范围、对应输出验收；无差别去文字化不入批次 | planned | 待指派 / — |
| <a id="rev-24"></a>REV-24 | 运营采集 | REV-17 | 有明确分析用途才启动事件采集；记录事件口径/保留边界/实际采集验证 | planned | 待指派 / — |
| <a id="rev-25"></a>REV-25 | 运营闭环 | REV-17, REV-23 | 问题—变更—发布—效果复核链；样本不足明确记载，不能宣称因果收益 | planned | 待指派 / — |
| <a id="rev-26"></a>REV-26 | IDML 试点 | REV-20 | 原生 IDML 验收证据及扩展/继续打磨/暂缓的明确决定；IR 测试不能替代 | planned | 待指派 / — |
| <a id="rev-27"></a>REV-27 | 恢复交接 | G2, REV-09 | 恢复或冷启动实测、环境/凭据/交接缺口和处置；不复写为生产恢复成功 | planned | 待指派 / — |
| <a id="rev-28"></a>REV-28 | 多格式扩展 | REV-26 | 仅在 IDML 原生验收通过且决定扩展后，记录各格式代表族验收；暂缓不得进入 | deferred | 待指派 / — |
| <a id="rev-29"></a>REV-29 | 多语言传播 | G3, REV-14, REV-15 | 语言变更、适用范围及版本关联的传播验收；遵守 Workstream V 设计门槛 | deferred | 待指派 / — |
| <a id="rev-30"></a>REV-30 | 操作交接 | G3, REV-16, REV-27 | 受支持入口/运行任务及人工操作减少证据；凭据/通知/恢复职责明确 | deferred | 待指派 / — |
| <a id="rev-31"></a>REV-31 | 协作验收 | REV-30 | 真实参与者独立操作审核/异常/交接记录；未找到参与者保持阻塞 | deferred | 待指派 / — |
| <a id="rev-32"></a>REV-32 | 内容服务 | G4 | 有消费团队、质量负责人、维护容量后才对接；记录实际消费场景和责任承接 | deferred | 待指派 / — |
| <a id="rev-33"></a>REV-33 | 内容接口 | REV-32 | 消费者验证带版本、适用范围、来源引用的导出/接口，并追踪一次真实修订 | deferred | 待指派 / — |
| <a id="rev-34"></a>REV-34 | 条件性架构 | REV-22, REV-30 | 仅实测吞吐/权限/维护瓶颈及获批专项决定触发；无触发可长期 deferred，不算欠债 | deferred | 待指派 / — |

REV-28–34 的初始 deferred 理由：前置试点、维护能力或消费需求尚未在本轮确认；
重启条件为该行依赖通过且对应业务/组织触发条件满足。REV-24 同样以明确分析用途为进入条件，
无用途时记录 deferred，不能为了勾完清单新增事件。原有审批和后置决定不被本台账覆盖。

首批入口整合由 REV-01/02/03/08 共同交付：统一出口、兼容旧链接、停止旧站独立更新、阻止目标站点再次分流。
REV-03 依赖对账及站点检查，不以 REV-10 中统计口径工作完成为前置，避免让无关运营工作延迟迁移。
REV-08 实施时先盘点已有检查，再确定缺口落在哪个现有入口；若涉及工作流文件，按仓库规则确认具体变更。
本次仅补齐任务契约，不表示机器检查或迁移已经完成。

## 3. 阶段门：以证据推进，Web 与 IDML 分开

| 门 | 范围与通过条件 | 当前记录 |
|---|---|---|
| G1 发布基线 | REV-01–12 验收；两条发布路径统一至 HT-Doc、旧入口实际兼容/停止独立更新、目标站点检查、对账及恢复证据符合方案 0–30 天出口 | 未验收 |
| G2 维护试点 | G1 通过且 REV-13–19 验收；跨代表结构发布、实际 TM 复用及区域试点证据可查 | 未验收 |
| G3 Web 扩展 | G2 通过且 REV-21–25、REV-27 验收；每目标维护负担及问题到发布链可说明 | 未验收 |
| IDML 独立门 | REV-20 定义原生验收，REV-26 记录实际结果及扩展决定；只有原生通过且决定扩展才启动 REV-28 | 未验收；不阻塞独立 Web 交付 |
| G4 协作与服务准备 | G3 通过且 REV-29–31 验收；真实交接参与者和维护能力到位；REV-32 另需消费团队与质量责任人 | 未验收 |

阶段中有条件项未触发或发生阻塞时，不自动改成完成。若确需其他工作先行，操作者须在下表
记录有边界的范围调整：保留原状态，明确风险、受影响后续项、责任人与重启条件。
后续只能消费被批准通过的范围；不能把局部放行表述为整个阶段验收通过。
IDML 原生验收失败或暂缓只阻止其自身扩展，不反向撤销已有 Web 验收。
REV-34 是条件性专项，不是所有路线结束前必须完成的任务。

| 决定日期 / 操作者 | 涉及 ID / 阶段 | 调整原因与证据 | 允许继续的范围 / 仍阻塞范围 | 责任人 / 重启条件 |
|---|---|---|---|---|
| — | — | 尚无范围变更或例外放行 | — | — |

## 4. 当前续接点

- 本轮（2026-09-19 REV-07 开工）：REV-08 翻 done（#1193 合入 `b0f60e53` + 全量绿跑 run 35451362215 + 哨兵 HD#91 关，验收原话「合并 验收」在册）。REV-07 M2+M1 首切片交付进 verifying：`tools/ops_catalog_sync.py`（sync=运营表机器列幂等 upsert、人工列不碰、失败行独立重试；reconcile=manifest↔运营表↔构建表回执三面核对+白名单分类 exit 0/1）、白名单种子=rev06 M0-05 的 49 个 Git-only 无回执 target、实跑=运营表 row20 JE-1000H/EU/en 陈旧 built_at/commit 已授权刷新（52 行不变，回读齐，reconcile exit 0），日志=[revitalization/rev07_m2_log.md](revitalization/rev07_m2_log.md)。
- 上轮（2026-09-19 收口）：0–30 天批次 REV-01/02/03/04/05/06/10/11/12 九项验收翻 done（验收单 [revitalization/rev_acceptance_20260919.md](revitalization/rev_acceptance_20260919.md)）；六项操作者决定全部执行完毕（旧站已删、运营表补行、翻译三刀落库、HTML_link 嵌套+每日校验 cron、M0 三项写、AC 按 2000E）。批次外：JE-2000E-KR re-seed 回退轮全闭环。
- 开口（不阻塞验收）：① KR 未路由评审编辑 5 组待路由拍板；② F6 본 제품 通扫 ~4 组归下一 F6 批；③ 37 条 TM 未解析候选的建行授权归十月批次；④ 反向候选 1ef29f0b8796 已压制不得再 approve；⑤ 存量 49 target 是否补录队列回执待操作者 M2 决策（白名单已压为已知差异）。
- 下一候选：REV-07 姊妹切片（HTML_link 写回后移到部署验证之后）→ REV-07 验收；**REV-09**（依赖 REV-07/08 验收）；REV-13 起等 G1 阶段门（=REV-01–12 验收）。
- 建议排队的新条目：错误码"专属码数<通用码数"check 告警（防 #955 语义再踩）；JE-1000F US 补 fr/es（REV-21 便宜候选，含 led-light 缺口修复）。

## 5. 实施 PR 与检查节奏

实施 PR 描述至少包括：`Task ID`、本次范围、前置项/阶段证据、产物和验证、回退、未完成项、台账更新。
收到“继续”时按第 1 节续接；任务执行期间在每轮结束、每次 PR 合入/发布验收后核对台账。
方案要求的每周复核由指定执行人执行：检查无责任人事项、长期 active、阻塞缺少解锁动作、
verifying 无验收和原方案条目遗漏。当前未配置自动周检，不能声称会自行提醒。

文档改动运行 `python3 tools/check_doc_link_integrity.py` 和 `git diff --check`；
每个实施切片另按仓库规则运行对应检查。评审时逐项确认：

- 方案 ID 集合与台账 ID 集合完全一致，无重复、无遗漏；依赖引用均存在且无循环。
- active 项依赖已通过，执行人和范围明确；done 项有验收记录且不依赖未完成项。
- 阶段门结论可回溯到对应任务；例外仅释放批准范围，deferred/cancelled 不计为 done。
- PR 变化符合所声明任务；代码、表写入、发布、验收结果各自有证据。

## 6. 给下一次执行的指令

> 先读 `code-as-doc/optimization_project.md` 和 `code-as-doc/dev/manual_revitalization_execution.md`，
> 核对主线、在审 PR 及当前续接点。优先完成现有 active/verifying 任务；否则选择依赖满足的最早 REV-ID。
> 开工登记执行人、准确范围和验收方式，只执行当前已授权的部分。结束前更新状态、证据、阻塞和下一步；
> 前置验收不通过不跳阶段，未完成项不得勾成 done，范围外发现先登记后决定。
