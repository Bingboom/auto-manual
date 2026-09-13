# 欧英规英文 Web 首批三本：调查与执行 Checklist

状态：调查完成，实施待执行。本 PR 只提交计划，不表示三本已构建或上线。

调查日期：2026-09-06。工程基线：`ef45a0df`（main，PR #1062）。

## 1. 目标、范围与权威内容

- [x] JE-1000F 已有：作为现有组件、公共 IR、样式和发布流程的回归基线，不重复接入，不计入本批新增交付。
- [x] 本批仅新增 `JBP-3600A / EU / en`、`JS-100I / EU / en`、`JA-AD01A / EU / en` 三本。
- [x] 欧英规指 EU/UK 适用内容，首期仅英文。仓库语言键为 `en`；不能把 `config.eu-uk.yaml` 的乌克兰语误当英国英语。
- [x] 操作人决定：与现行发布版重合的内容，直接采用现行发布版；不做新旧版本差异审计，不逐段询问采用哪个版本。
- [x] AI/TXT 是接入材料。正文和参数进入结构源；插图采用对应型号、地区、语言的带字整图；包装清单、规格、警示保持共享组件。
- [ ] 每个目标登记 EU/UK 适用范围；若确有不同插头/市场图，绑定准确资产，不能用 US 或 JP 图片代替。
- [ ] 三本均获得正式网址、发布版本、来源记录、冻结 IR/素材及验收记录，才关闭本批。

本批不开展其他语言、IDML 原生分页、全仓重构或 IR 第 5–7 刀的全面收口。出现阻塞三本的公共缺口，按下文最小范围修复。后续语言沿用相同 slot/component 身份，替换文案和对应语言插图。

## 2. 已调查的工程基线

| 事实 | 证据与影响 |
| --- | --- |
| 整本 Web 已使用公共 IR | [word_bundle_html.py](../../tools/word_bundle_html.py) 的 Web 分支经 [web_document_source.py](../../tools/web_document_source.py) 生产，再由 [web_document_ir.py](../../tools/web_document_ir.py) 重放；新包为 `manual-ir/v2`、`whole-document-components/v1` |
| 已嵌入 14 种组件 | [whole_document_components.py](../../tools/manual_ir/whole_document_components.py) 与 [web_embedded_components.py](../../tools/web_embedded_components.py) 已覆盖 Callout、Spec、Inbox、Overview、FCC、Operation、LCD Mode、Warranty 三种、LCD Icon、Troubleshooting、Symbols 两种；不用重建一套 Web 组件 |
| 共享并未等于四端全部闭环 | [IR 收口记录](ir_document_closeout.md) 明确保留 App/reference figures、presentation 分层及旧兼容路径；本批不以全部退休为上线前提 |
| BP 国际骨架已存在 | [bp-intl blueprint](../../docs/manifests/skeletons/bp-intl/blueprint.yaml) 与 slot templates 可复用；当前 [config.bp-eu.yaml](../../configs/config.bp-eu.yaml) 仅登记 JBP-2000B，并按六语合并产出，不能直接声称支持 JBP-3600A 单语 |
| BP 源文必须按目标选章节 | 现有 blueprint 把 operation/troubleshooting/storage 列为 required；JBP-3600A 发布英文目录不是这份完整序列。要作目标章节映射，必要时改成有证据的可选 slot；不能带入 JBP-2000B 的章节和配套主机名称 |
| 三个新目标尚无已提交接入配置 | 本次搜索 configs、manifests、templates、recipes 未定位到这三个型号的生产接入；JS-100I 仅在目录查询测试出现。此结论限定 Git 工程树，不代表实时源表没有记录 |
| 太阳能板/充电器需要类别结构 | 已提交 skeleton 目录只有 bp-intl、bp-jp；不能拿 MAIN 的 LCD、UPS、App 等章节硬套太阳能板或充电器 |
| Inbox 有确定的五项阻塞 | [inbox.py](../../tools/component_specs/inbox.py) 与 [inbox_html.py](../../tools/component_specs/inbox_html.py) 限定三项；五卡最小复现返回 `HB-SPECIAL-INBOX: exactly three cards are required`。JS-100I 实际有五项 |
| 首段门禁假定有 IMPORTANT | [word_bundle_html.py](../../tools/word_bundle_html.py) 的 Web 分支拒绝非 governed preface 开头；短说明书需显式入口策略，不制造源文件没有的前言，不全局关闭保护 |
| 发布链路已存在 | [两平面图](../../user-guide/two_plane_map.md)：auto-manual 工程变更同步至 Hello-Docs；Web Publish 产生 `docs/publish/**` 快照 PR；Hello-Docs/main 经 RTD 构建。localhost、上传成功或已写 HTML_link 均不单独构成上线完成 |

### 2.1 本轮实际验证

- [x] `git fetch origin` 后，在独立干净检出使用仓库 start_branch 包装器创建本计划分支。
- [x] 聚焦测试 42 项通过：`tests.test_manual_ir_read_contract`、`tests.test_web_document_ir`、`tests.test_manual_ir_components`、`tests.test_bp_intl_eu_target`、`tests.test_queue_config_resolution`。
- [x] JE-1000F/EU/en 的 `build.py check` 通过，使用已提交 `tests/fixtures/phase2`，输出至隔离 staging；这验证基线源码，不是生产数据或正式站点重新验收。
- [x] 三个 AI 附件的下载大小与登记一致，PDF 兼容层均可读取；原生 Illustrator 编辑能力不在本次验证范围。
- [x] 本计划文档门禁通过：158 个 Markdown、1729 个链接，0 个断链；62 个热点模块的 maintainability guardrails 通过（0 个新增语言字面量问题，6 个既有 stale baseline 提示）。
- [ ] 本批真实 Web 构建、三目标 live source-table 读回与正式发布仍待执行。

## 3. 三本的输入与章节清单

入口：[钉钉源文件清单](https://alidocs.dingtalk.com/i/nodes/YndMj49yWjP03jNjCDojvAQdJ3pmz5aA?entrance=data&sheetId=97v7518)。
现行发布文件是本批接入的权威输入；读取、拆章和图文核对只验证接入完整性，不比较新旧版本优劣。

| 目标 | 已定位输入 | 实际接入重点 |
| --- | --- | --- |
| JBP-3600A（HTP011） | [现行 PDF](https://alidocs.dingtalk.com/i/nodes/NZQYprEoWoeAawzwfBwMeb25J1waOeDk)，V2.0-2026-08-04；PDF 45 页，英文正文物理页 5–12，另含共享前言与尾页。AI：`16-0102-000334 说明书 HTP0113600A-EU-JAK RoHS REACH.ai`，10 个兼容页 | 安全/符号、3 项 Inbox、产品示意、LCD、连接/锁扣、AC/太阳能充电、规格、质保；按发布版纳入前言、尾部适用内容。配套主机为 Explorer 3600 Plus，不继承 2000 Plus |
| JS-100I（HTS006） | [现行 PDF](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3XrMnMUONl9pAxJkb4Mw9r)，V2.0-2026-04-01；PDF 50 页，英文正文物理页 4–12，另含封面/目录/尾页。AI：`16-0102-000209 说明书 HTS006100C-EU-JAK RoHS REACH.ai`，10 个兼容页 | Safety Tips、5 项 Inbox、正反面/支架、展开、折叠、DC8020/DC7909 连接、连接器、角度指示、技术参数、质保；不接主机 LCD/UPS/App |
| JA-AD01A（HTO847） | AI：`(翻译用）38-0001-000880 HTO847-EU-JAK 102W充电器 说明书 RoSH REACH.ai`，9 个兼容页，英文印刷页 01–06；配套 TXT 可读。当前源清单“当前纸质说明书”未返回链接 | 3 项 Inbox、USB-C1/C2/A 端口示意、单口/双口/三口输出和 PPS 分组、使用图、警告与源文件已有尾部内容；不能把 102W 总功率误分配给每个端口 |

JA-AD01A 发布版定位状态：2026-09-06 对同 Base 的“05-01-发布资料”分别查询 `JA-AD01A`、`HTO847` 未返回匹配；关键词查询可能受字段范围影响，**不据此认定发布版不存在**。实施 A 阶段应通过项目/资料业务/包材关联进一步定位；仍未定位时只暂停该目标发布，不阻塞另外两本。

BP3600 的关联 PDF 文件标题写 JBP-3000A，但可见封面、AI 和表内型号均为 JBP-3600A：按正文正确身份绑定，保留命名债务，不改外部文件、不做新旧对比。

### 3.1 已读取文件的 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| BP3600 现行 PDF | `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe` |
| BP3600 AI | `e0ccc33427f89c77c30d32e073a3027123f4c8a9c9f5029d2378172a7f0a3761` |
| 100 Air 现行 PDF | `cec27af653d9f5da11d641e2431ddc0b71ced186bbadfd9594fa8cd9c96e1596` |
| 100 Air AI | `5d7ded6ba7810505cfb4c91b128a71cbef16a0e11aae720cdbd887559224b96a` |
| 102W AI | `0252cb5db68fb67b3fe0947824de4655e13e26f90b3dde1f6bada3b64aa390fc` |

正式执行时将输入存入受管素材/源快照位置，不能依赖本机临时路径或会过期的签名下载 URL。仓库只记录稳定来源、版本、recipe、绑定和 hash，按现有约定管理二进制。

## 4. 依次执行的 Checklist

### A. 固定三个目标输入与基线（预计 0.5–1 天）

- [ ] 固定执行时 main commit；核实 JE-1000F/EU/en 的现有目标、审稿版本与已发布入口，将它列为回归样本。
- [ ] 对三目标查询实时源表与业务构建记录，逐项记录已有/缺失的参数、占位参数、素材、review 状态、Version、Git_ref、Build_family。不得从 fixtures 推断活库情况。
- [ ] 为三目标完成 source → chapter/slot → component/figure 映射；同页多个章节按语义拆分，保持原顺序。
- [ ] 固定英文发布版优先规则；定位 JA-AD01A 发布资料链路。有现行内容即直接采用，不建立版本对比任务。
- [ ] 映射内部目标为 `region=EU, lang=en`，业务语言范围使用 `eu-en`；验证 EU/UK 适用信息与图片，不增设误指乌克兰语的英国配置。
- [ ] 使用现有主数据/本地快照字段承载内容；本阶段不改 phase2 schema。需要 live 写入时按源表流程提交具体候选，获准后逐记录写入、读回。

交付：三份输入登记、章节映射、素材目录、源表缺项清单；阻塞项只挂对应目标。

### B. JBP-3600A：复用 BP 国际骨架（预计 1.5–2 天）

- [ ] 用 `bp-intl` 蓝图和 target plan 表达发布版章节；为本书没有的 operation/troubleshooting/storage 独立章节作实际映射，不能补造内容或复用 2000B 段落。
- [ ] 若现有 required slot 阻碍真实结构，只在蓝图/plan 数据契约作最小通用扩展，验证 JBP-2000B US/EU 的原清单保持稳定；不在 skeleton resolver 加型号判断。
- [ ] 建立可复用 BP/EU/en 家族入口和 JBP-3600A 精确目标登记。保持原六语 BP/EU 路线；不是复制整份 JBP-2000B config 后替换名字。
- [ ] 将容量、重量、尺寸、配套主机、连接数量等作为本目标数据写入已有契约；语言文案复用不等于产品参数复用。
- [ ] 接入现有 Callout、Symbol、3-card Inbox、LCD 和 Spec；源版质保结构匹配现有变体才使用该变体，不能强套 JE-1000F 年限与分节。
- [ ] 产品示意、连接/锁扣、充电图以英文带字整图接入；不强套 JE-1000F Overview 的坐标和端口。
- [ ] 通过全部构建和验收后，单独发布此目标；无需等另外两本完成。

### C. JS-100I：太阳能板结构与五项共享 Inbox（预计 2–3 天）

- [ ] 创建可复用太阳能板类别的章节声明与英文 slot 模板；用 manifest/recipe 接入现有 assembly，不增加第二套正文解析器。
- [ ] 将实际无 IMPORTANT 前言的情况声明为入口策略：按目标结构允许 Safety Tips 等真实首章；保留现有 JE-1000F/BP 的 preface 约束。禁止造空前言或全局取消门禁。
- [ ] 为 `HB-SPECIAL-INBOX` 增加可变项数变体，保留已有 three-card 读取兼容性；更新 schema/registry、source parser、IR asset roles 与 Web adapter。
- [ ] 五项准确为太阳能板、收纳袋、3m 多功能充电线、DC8020→DC7909 转接头、用户手册；保留充电线仅适用于 JS-100I 的 Note。
- [ ] 三卡与五卡进入同一公共组件族，标签保持可搜索文本；不截整张包装清单，不复制 solar 专属 Inbox 渲染器。
- [ ] 在组件注册中诚实声明其他 renderer 对新变体的能力；不要因旧三卡支持就声称 IDML/Word 已支持五卡。无需为本批完成新变体印刷排版。
- [ ] 展开、折叠、连接、角度指示采用各自完整带字图；标题和正文仍来自结构源；整图覆盖文字的去重必须有明确绑定，不能按相似文本随意删除。
- [ ] 参数按本书技术参数分组，保留 STC/BNPI、上下标、单位和注释；不使用主机电池规格字段填充占位。
- [ ] 验证桌面五卡布局与手机重排、图片放大可读性，完成单目标发布。

### D. JA-AD01A：短说明书与分组输出表（预计 1–2 天）

- [ ] 沿资料业务/项目/包材关联定位现行发布版；未找到之前，将 AI 接入明确标为候选，不能标成正式版本已验收。
- [ ] 使用可复用充电器/配件类别章节声明；只包含真实章节，复用 C 阶段入口策略，不复制主机清单。
- [ ] 接入三卡 Inbox，确认包装中为充电器、100W 充电线、手册；保留正确 EU/UK 产品外观图。
- [ ] 单口、双口、三口与 PPS 输出使用共享语义表格，组合名称与各端口行有明确层级；若现有 Spec schema 不支持该分组，增加数据驱动变体，不在 Web 渲染器里写 JA-AD01A 条件。
- [ ] 使用完整端口/连接插图，保留产品外观英文和参数；正文警告原文入库，不套用主机警告或自行改写数值。
- [ ] 不新增源文件没有的 LCD、UPS、充电储能或 App 章节；质保/尾部仅按定位到的发布版安排。
- [ ] 参数分组、警告、长表格手机显示验收通过，且发布权威输入已确认后，完成发布。

### E. 每一本都必须通过的完成门槛

- [ ] runtime 或已有 review 路线明确；已有审稿目标的数据更新优先 `sync-review`，不擅自重播种覆盖审稿内容。
- [ ] 章节/语义块覆盖完整，无 RST 指令、未替换变量、重复画板内容或解析丢段。
- [ ] source → IR 的目标、语言、顺序、ComponentSpec 与资产引用一致；新包写 `manual-ir/v2` / `whole-document-components/v1`。
- [ ] 单独复制 IR 与素材包后，禁止读 RST/CSV/活库，仍能重放；资产缺失/改 hash 必须失败。复用现有 cold-replay 测试方法，不写第二个生产重放器。
- [ ] `web-illustrations/v1` 绑定正确型号/地区/语言、文件和 SHA-256，covered annotations 的变化仍会拦截陈旧图；纯图存在可读 alt。
- [ ] 桌面与 375px 手机视口检查：图片、目录锚点、表格横滚、清单、警示、脚注和链接；页面整体无意外横向溢出。
- [ ] 修改共享代码后重跑 JE-1000F/EU/en；修改 BP 契约后增加 JBP-2000B/EU 回归。原文、卡片数、表格和资产绑定没有非目标漂移。
- [ ] 在 Hello-Docs 使用准确 record/Document_Key/Version/Git_ref 执行 Web Publish；候选 PR 只含 `docs/publish/**`，保留已上线其他目标。
- [ ] 发布 PR 按仓库授权流程合入后，核实 RTD 构建成功、正式 URL 实际可读、目录入口可达、图片和链接正常；仅 HTML_link 已填不能打勾。
- [ ] 在现有交付记录登记来源版本/hash、工程 SHA、发布 PR、正式 URL、验收结果与剩余债务；修订从结构源回写，不手改生成 HTML。

## 5. 分支、PR 与排期

预计总投入 6–9 个工作日，基于本次源码与文件调查估算；未以三目标真实生产计时。B 完成后按接入/素材/验收工时校准。JA-AD01A 权威输入等待单独记录，不让它阻塞 B/C。

| 顺序 | 工程 PR 内容 | 依赖与停止边界 |
| --- | --- | --- |
| P0（本 PR） | 调查、checklist、下一步路线入口 | 只改文档；不开 live 发布、不改源表 |
| P1 | JBP-3600A EU/en 的 BP 家族配置、slot/data/asset 接入 | A 完成；公共 BP slot 修复有跨目标证据后一起验收 |
| P2 | 共享可变项数 Inbox 与可声明首章入口 | 保留 JE-1000F 三卡及前言行为；仅实现 C/D 所需最小合同 |
| P3 | JS-100I EU/en 类别结构、正文、五卡与带字图 | P2；如需新增骨架声明，按类别复用，不按型号复制 |
| P4 | JA-AD01A EU/en 类别结构、数据/素材与输出表 | P2、发布版定位；分组规格变体若超出目标接入，单独小 PR |
| 每目标发布 PR | Hello-Docs 的冻结 Web 快照 | 对应工程已同步、数据已核实、E 通过；独立审核与发布 |

逐个分支从最新统一 main 起步；本计划不要求另外开启代理任务。不把整批源码合到 Hello-Docs；工程变更通过现有镜像同步，业务面只提交发布快照。

## 6. 验证命令与证据要求

以下命令使用已安装的项目 Python 环境。单测/静态检查按实际变更执行；纯文档计划无需假称全套产品已构建。

```bash
python -m unittest tests.test_manual_ir_read_contract tests.test_web_document_ir tests.test_manual_ir_components tests.test_bp_intl_eu_target tests.test_queue_config_resolution
python build.py check --config configs/config.eu-en.yaml --model JE-1000F --region EU --data-root tests/fixtures/phase2 --staging-root /tmp/web-three-plan-baseline
python tools/check_doc_link_integrity.py
python tools/check_maintainability_guardrails.py
```

实施修改 Python 后，补全根 AGENTS 要求的 Ruff、全量 unittest；涉及 utils 类型再跑 mypy。新三目标须提交各自最小可信 fixture，不能用 JE-1000F fixture 冒充真实目标数据。

新家族配置的最终路径在 P1/P3/P4 落地后登记。以下是执行模板，`$TARGET_*` 必须替换为该目标经确认的配置、型号、快照和隔离输出路径，不是目前已跑通的命令：

```bash
python build.py check --config "$TARGET_CONFIG" --model "$TARGET_MODEL" --region EU --lang en --data-root "$TARGET_SNAPSHOT" --staging-root "$TARGET_STAGING"
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config "$TARGET_CONFIG" --model "$TARGET_MODEL" --region EU --lang en --data-root "$TARGET_SNAPSHOT" --staging-root "$TARGET_STAGING"
```

Web profile 环境变量来自现有 [queue_build_execution.py](../../tools/queue_build_execution.py)；普通 `md` 的成功不能代替 Web profile 验收。正式发布复用 [现有发布流程](../build_doc_guide.md) 和 [两平面约定](../../user-guide/two_plane_map.md)，不添加第二套部署命令。

## 7. 防偏移与里程碑交付

- [ ] 新增产品只增加目标数据、类别/slot 声明、素材 recipe/绑定；若还需改公共渲染，记录可复现合同缺口及跨产品回归。
- [ ] 新机制迁移本批实际调用方；记录旧路径退出范围，不用“添加了 helper”作为完成标准。
- [ ] 未消除的 v1、App/reference/presentation 债务明确留在原路线，不用本批计划宣称 IR 全面收口。
- [ ] 三本正式 URL、来源及版本、IR/hash、发布 PR 和验收证据齐备；JE-1000F 回归仍通过。
- [ ] 汇总每本接入/素材/验收耗时，给表内剩余产品排期；完成时更新本 checklist，并在维护日志记录本阶段完成。

完成定义：**以 JE-1000F 的既有公共 IR 和 Web 产线为基线，新增三种产品的欧英规英文说明书，实现从权威内容到结构源、共享组件、冻结 IR、正式网页和可追踪更新的闭环。**
