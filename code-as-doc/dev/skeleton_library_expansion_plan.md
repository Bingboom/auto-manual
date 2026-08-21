# 骨架库产线拓展执行方案（Skeleton Library Expansion Plan）

Status: **v2 纵向切片版** — 待操作者批准 · Owner: 夏冰 · 2026-08-21（同日改向）

机制设计在
[`../architecture/Product_Skeleton_Library_Design.md`](../architecture/Product_Skeleton_Library_Design.md)，
证据在 [`../architecture/manual_ia_audit_2026-08.md`](../architecture/manual_ia_audit_2026-08.md)，
逐 PR 执行清单在
[`../next_optimization_checklist.md`](../next_optimization_checklist.md) 的 Milestone M。

## 0. 两条前提认知

1. **出货书 = 管线产物 + InDesign 手工层。** 模板零命中的块是排版时手放的，不是印不出来。
   差集分两类：管线缺口（本方案修）与手工层承担项（fragment 化收编，是债不是急件）。
2. **路线是纵向切片，不是横向波次**（操作者 2026-08-21 裁决）。v1 的 B0–B9 波次
   每层做完再下一层，把"这套骨架库能不能产出一本能印的书"推到最后才验证——
   Workstream H 正是横向铺到一半被回滚的。改为：**先窄地打穿全链一次，
   概念证实后再铺开**。原波次内容降级为铺开期参考（§7）。

## 1. 切片定义（操作者七步 → 落地）

| 操作者的步 | 落地 | 清单项 |
| --- | --- | --- |
| 1. 三层：Skeleton Blueprint / Product Manual Plan / Resolved Manifest | Blueprint 落盘为 `docs/manifests/skeletons/<cell>/blueprint.yaml`；Plan 是解析产物（可 dump 审查，不落盘为源）；Resolved Manifest = 今天的 `manual_*.yaml` **字节兼容**，四渲染栈/review 派生物/版式 pin 只看这一层 | S1 |
| 2. 稳定 slot_id + order 护栏 | Blueprint 槽位带 `slot_id`；**新 manifest** 的物化名从 slot_id 派生而非迭代位置；既有 manifest 命名路径不动（`pNN_` pin 零风险） | S1 |
| 3. 最小 contract tiering | 只做机制 + BP 档：`page_contracts` 分档键 + `requires_capability` 组；14 个主机专属 row_key 入档。**不回收 JE-300E fork**（铺开期） | S2 |
| 4. 一个加电包作第二骨架实例 | **`JBP-2000B_US`**（HTP017 美加规，3 语 28 页），BP@INTL 格 | S1/S4 |
| 5. 抽一个低风险内容模块 | **`battery_long_storage_advisory`**（存放页尾段"长期存放/电池健康"告知），不是 UMI——见 §3 | S3 |
| 6. 跑通 PDF/HTML/Word/IDML | 四栈机械验收判据（§5），IDML 走 fallback 通路（无已批准版式也能出） | S5 |
| 7. 真实 InDesign finishing + 逐页对账 | handoff zip（既有机制）→ 操作者 InDesign 收尾 → 与真实出货书（28 页）逐页对账出报告 | S6 |

## 2. 切片目标为什么是 JBP-2000B_US（取证结论）

它是全仓**唯一**同时满足四条的加电包 document_key：
有 capability 行（`model_capabilities.csv` 三条 JBP 行之一，能力全 FALSE——
意味着 UPS/加电包扩容两页由**既有能力门零工作量自动落掉**）；多语言区规
（3 语，真的过语言编排这一关——语言轴占页数方差 82%，选日规单语会让四栈
"绿得没有信息量"）；同区配对主机 JE-2000E_US 有 50 行 Spec_Master 可克隆；
语料出货书 28 页可逐页对账，且与主机同开本（InDesign 复用同一文档设置）。

关键就绪度发现：**规格表只需 11 行数据，且 11 行全部映射到 JE-2000E_US
已在用的 row_key——零新词汇，纯数据克隆**（走既有 spec-intake 审批门）。
`validate_spec_master` 当前对该目标报 93 条，其中 12_app_setup 的 9 条随
BP 骨架不含 App 页自然消失，剩余集中在 03/05 两个 recipe 的 14 个主机专属
row_key——这恰好就是 S2 最小分档的确切工作面。

被否的候选（详见工作流产物 `wf_72e57478-50e`）：日规单语（无配对主机数据、
BP@JP 规范序列未定、语言轴不过）；欧英规 6 语（无 capability 行、54 页违反
"切片要窄"，**留作切片 #2**——同骨架只加 3 语，是最自然的铺开第一步）；
中规（无语料可对账）；HTP015（模板债翻倍 + 破 8 页块不变量）；HTP011
（单区规、槽序即分叉、且**文件名写 JBP-3000A 而封面是 JBP-3600A**——
语料建档缺陷 +1）；HTP007（10 页退化骨架，几乎什么都不暴露）。

## 3. 内容模块为什么换掉 UMI

Phase B 设计原定第一刀是 `user_maintenance_instructions`，但它在加电包
**0/7**——切片跑加电包根本碰不到它。裁断：**换模块，不换切片目标**
（加电包是唯一 0% 覆盖的品类、唯一逼出新 skeleton_family 的实例，
还同时压着 contract tiering / slot_insert / 语言轴 / target_defaults
四个下游门；换目标一次丢四个）。

新模块 `battery_long_storage_advisory`（"亏电存放 3–6 个月可能无法再充电…"
告知段）：加电包侧覆盖 **7/7 = 100%**（BP@INTL 每语言块出现两次，BP@JP 以
吸收态存在）；全库 10 份手抄副本、0 共享载体、0 占位符、0 品牌词、0 品类
名词、跨区规 100% 同文；无标题块不进目录、字节守恒可硬断言。它比 UMI 多
压测两件事：`untitled_block` 与 `absorbed` 两个呈现态（UMI 只有一态），
以及 `page_zh` 里现成的长短两个变体。UMI 降级为铺开期主机线模块。

## 4. 四渲染栈就绪度（取证结论）

| 栈 | 判定 | 切片内动作 |
| --- | --- | --- |
| LaTeX/PDF | 组件库全局一套零按目标分支；真门是 contract（S2 解决） | 零新宏（新增即超范围） |
| HTML | 唯一按目标耦合是 `figure_targets` 软白名单（只登记 JE-1000F/US）→ 新品类拿"朴素 HTML"，**是按设计降级不是坏** | 白名单不许扩 |
| Word | reference doc 绑 config 层（区规×语言包），与型号无关，最省事 | 无 |
| IDML | **能出**：无已批准版式的目标走 latex-auto fallback（`reference_layout_plan.py:714` docstring 明写），页数不设闸 | 见下面的红线 |

**IDML 的真陷阱不在出文件，在 `data/layout_params.csv`**：它是全仓唯一
一份共享单例，而 JE-1000F/US 的已批准版式把**整份 CSV** 进哈希——给加电包
加一行就会让那份批准态脱钩（#720 同型事故）。**切片红线：不碰
`layout_params.csv`、不碰任何已批准版式契约**；`connections`/`installation`
落 `UNCLASSIFIED_PROSE` 出警告，记为切片接受的降级，铺开期再解。

## 5. 切片验收（全部可机械判定）

1. `build.py check`（新 config × JBP-2000B × US）exit 0；unittest / ruff /
   guardrails 全绿。
2. **PDF 页数命中硬公式**：`pages = F(3) + 3×8 + 1 = 28`，差一页即未通过；
   `pdfinfo -l` 全页同尺寸；xelatex 日志零 Undefined control sequence。
3. HTML：web_publish 三步（check → md → html）exit 0；新页种每语言各有
   `<section>`；对新目标 grep `hb-*-composition` **必须零命中**（有命中 =
   白名单被误扩，退回）。
4. Word：构建 exit 0，走朴素结构。
5. IDML：fallback 导出成功产出 `.idml`；`git diff data/layout_params.csv
   docs/renderers/contracts/reference_layout/` **必须为空**。
6. **回归**：JE-1000F/US 与 JE-1000F/JP 两条主机线 staging 双目录比对
   逐字节不变（M-pre.4）。
7. S6 对账报告落盘：与出货书逐页比对，差异分类为
   管线缺口 / 手工层承担 / 数据缺口 / 接受的降级，各自计数。

## 6. 切片明确不做

JE-300E fork 回收（S2 只建机制）；既有 manifest 的语言块参数化（B1，
新 manifest 由解析器自带展开，既有 17 份不动）；App/联网能力列（BP 蓝图
直接不含 App 槽，不需要它）；主机侧 10 份模块副本的收敛（S3 只让 BP 消费
模块并证明层能用，收敛留铺开期做字节比对）；`layout_params.csv` 与任何
已批准版式的改动；authoring 权翻转（解析器是"生成后验证"，YAML 仍是真相源）。

## 7. 铺开（切片验收后再排期）

v1 的三波（语言块参数化 B1 / 日规中规修真 B3-B4 / contract 全量分档与
JE-300E 回收 B7 / page_registry 权威化 B6 / 合规 fragment 库 B8 / 收尾 B9）
在切片验收后按切片学到的东西**重新裁尺寸再排期**，逐项仍受
Milestone M 的 M-pre 公共规则与既有 workstream 接线（Q/V/T-K4）约束。
已做过可执行性核验的逐项细节保留在 Milestone M 的铺开积压段。

## 8. 操作者的门

1. 批准本切片方案（S1 即可开工）。
2. S4 的 11 行规格数据入库（既有 spec-intake 审批门 + 逐写回读）。
3. `connections`/`installation` 两个新模板的文案审校
   （内容来源 = HTP017 美加规出货书印张 04，法务文本另签）。
4. S6 的 InDesign finishing 一轮 + 对账结论裁决。

## 9. 修订记录

- 2026-08-21 v2：按操作者裁决改为纵向切片（七步）；切片目标 JBP-2000B_US、
  内容模块 battery_long_storage_advisory（UMI 因加电包 0/7 降级）；
  IDML 红线 = 不碰 layout_params.csv；波次降级为铺开期参考。
- 2026-08-21 v1：三波 B0–B9（已被本版取代，细节存 git 历史与 Milestone M 积压段）。
