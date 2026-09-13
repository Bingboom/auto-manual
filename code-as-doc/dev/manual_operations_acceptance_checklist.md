# Manual Operations Acceptance Checklist

Status: batch Web rollout first; structured operations deferred / umbrella PR stays **Draft**. Updated: 2026-09-13.

Umbrella: [#1103](https://github.com/Bingboom/auto-manual/pull/1103).

## 0. 最新执行顺序：先批量网页化，后结构化运营

操作者最新决策（2026-09-13）：「是的 以清单内说明书的批量网页化为主线」。
本节覆盖旧计划的执行优先级，不抹去已完成工程证据，也不将 deferred 改成 completed。

- **近期主线**：只处理操作者指定的[钉钉清单](https://alidocs.dingtalk.com/i/nodes/YndMj49yWjP03jNjCDojvAQdJ3pmz5aA?iframeQuery=entrance%3Ddata%26sheetId%3D97v7518%26source%3Dnotable_portal%26viewId%3DxWo5UbG&sideCollapsed=true)。
  以操作者提供/确认的 PDF 发布版为准，先完成可复现的 Web 源、含字整图、
  原生 HTML 表格、共享组件和 RTD 上线。不扩入 HTO2682 或其他清单外目标。
- **发布路径**：复用既有 Git-only 路径（冻结来源/资产/版本 →
  Hello-Docs 的 docs/publish-only 发布 PR → main → RTD）。
  不要求先建云文档、不要求先抽齐或录齐线上结构化数据、
  不要求先创建/武装 Web Publish 队列；不是绕过 PR、内容和资产验收。
- **后续治理**：逐本抽取结构化数据，映射共享骨架与产品绑定，
  再接入云文档审稿 + Publish，以及 Web Publish 的长期维护流程。
  骨架执行仍归 Milestone M，不复制第二套骨架任务。
- **保留追溯**：每本记录型号、市场、实际语言、PDF 发布版本/来源哈希、
  可复现 Web 输入及正式 URL；后续数据驱动迁移保留原 URL 或显式兼容跳转。
  这是最小发布身份，不是提前复制全部正文到线上表。
- EU/UK 共用手册，入口暂以 EU 默认；只启用真实已发布语言，
  12 语回稿陆续接入，不等待齐套才上线，不把混语标成单语。

### 近期 checklist（不冒充长期运营验收）

- [x] 操作者确认“清单批量网页化优先，结构化治理和正式队列后置”。
- [ ] WEB-B01：重新对账清单与当前 RTD 冻结目录；逐条标记已上线/待修正/
  待构建/缺输入，登记版本、实际语言和 URL。历史“20 条/21 出版物”不能替代本次对账。
- [ ] WEB-B02：对清单内剩余或需更新项核对 PDF 发布版；已有线上成果复用，
  不重复构建无变化手册。缺文件/适用市场/翻译时明确列缺口，不推断新事实。
- [ ] WEB-B03：按批复用既有 Web 骨架与样式；Overview/操作/充电使用语言匹配的
  含字整图（含 On/Off/引线），表格保持原生 HTML，质保数字组件统一复用。
  完整抽取线上结构化数据及 #1101 合入均不是所有手册的前置门。
- [ ] WEB-B04：每批验证内容/资产/链接及桌面、移动阅读；实现或内容变更独立 PR，
  按有效授权和全绿门禁合入，只通过限定的 Git-only 发布路径上线。
- [ ] WEB-B05：读回 RTD 实页并更新清单覆盖证据；保留已有链接、其他型号和语言，
  记录 PDF 版本、发布 commit、URL 及剩余缺口，不以本地预览代替上线。
- [ ] WEB-B06：近期目标范围内可用输入全部完成上线/纠错，未回稿和缺输入明确列账；
  形成后续逐本结构化治理的优先队列。

### 暂缓而非取消

OPS-04 工作流接线/线上链接回填、真实队列创建或武装、反馈闭环与后台运营
不是 WEB-B01～06 的前置条件。本轮刚开始的 verified-web-release 隔离修改已暂停，
未创建实现 PR、未合入、未创建或触发新发布记录。不得因旧“继续”指令自动恢复；
只有操作者重新启动该治理阶段才继续，并保留各独立门禁。
反馈渠道仍待确认，不启用新的收集服务。


唯一合并条件：**实现 manual 运营的打通**。建好首页、代码合入、CI 绿或生成
本地样例均不等于闭环验收。每完成一个独立切片，开实现 PR；合入并完成该切片
验收后，才在本文件勾选并登记 PR、commit、命令结果和部署证据。

## 1. 原始运营 discovery（历史基线，当前结果见证据账本）

- 基线：auto-manual/main `a55d666d6d22b713346d3a6bcd7884e7c0395dc8`。
  [#1102](https://github.com/Bingboom/auto-manual/pull/1102) 已交付首页；
  RTD build `34531930` 成功。默认 EU；EU/UK 共用 EU 手册，US 独立。
- [发布装配](../../tools/publish_branch_assembly.py) 的 target 含 lang，
  但 route 仍为 model/region/md，同一区域多语言会互相替换；必须先修身份，后接入口。
- [链接回填工作流](../../.github/workflows/feishu-web-publish-queue.yml)
  在候选 PR 合入之前执行 HTML_link 回填，不能作为真实上线证明。
- [门户](../../tools/rtd_portal.py) 目前从冻结 index 链接生成卡片，
  尚无多语言发布分组；计划语言不等于已发布语言。
- [#1079](https://github.com/Bingboom/auto-manual/pull/1079) 有单语包投影，
  优先审计复用，不重建第二套语言拆分器；历史 CI 不代表最新 main 兼容。
- RTD 只消费 Hello-Docs/main 冻结发布快照；代码只在工程面演进。
  遵守[双平面地图](../../user-guide/two_plane_map.md)。目录是可重建读模型，
  不把全部正文复制到新的线上表，也不让目录成为内容源。

非目标：等待全部 12 语回稿、重做四端渲染、引入 OSS/新后台/付费服务、
把清单外品类纳入试点。骨架与数据接入继续归
[Milestone M](https://github.com/Bingboom/auto-manual/pull/974)；
[#1083](https://github.com/Bingboom/auto-manual/pull/1083) 的跨端债、
[#1084](https://github.com/Bingboom/auto-manual/pull/1084) 的资产对账、
[#1101](https://github.com/Bingboom/auto-manual/pull/1101) 是依赖/独立工作，
不在此复制其执行清单或擅自合入。

## 2. 后续运营实现切片与验收（未完成项 deferred，不阻塞近期批量网页化）

- [x] OPS-00：完成发布身份/回填顺序/门户基线 discovery，登记独立授权 MA-066。
- [ ] OPS-01：复用现有单语投影，确认可用语言来自实际冻结内容，缺译失败或明确不可用；
  不把混合语全文标为单语。范围：语言 bundle/helper 与测试；不引入 Chrome/PDF 依赖。
  - [x] OPS-01a 内部 helper 复用与安全回归：#1104 已合入；不等于发布集成完成。
  - [ ] OPS-01b 接入真实单语发布输入，验证正文/含字图语言及独立 URL。
    - [x] OPS-01b1 Web 显式语言的 canonical RST 接线：#1111 已17/17全绿合入；check/md/html 共用投影，不改变队列。
    - [ ] OPS-01b2 封存投影证据并校验后，才允许发布元数据晋升 single；完成真实独立 URL 验收。
      - [x] OPS-01b2a 语言证据绑定不可变 Markdown/HTML release：#1113 已合入 `0a910a3e`；真实双语线上 URL 仍待验收。
      - [x] OPS-01b2a 工程凭据绑定：#1113 已17/17全绿合入；check/md/html投影凭据与不可变版本、元数据、stored重放绑定，修复review pre-sync完整源解析。
      - [ ] OPS-01b2b 使用正式批准的源/含字图完成真实独立语言URL验收；本地fixture通过不算上线。
      实施边界：check/md/html 三步比对同一 canonical manifest 摘要；封存完整 RST
      引用闭包与 Markdown/HTML 摘要；metadata writer 和 assembly 各自验证后才接受
      single，缺失/漂移/身份或路径不符须在晋升前失败。旧无证据输入保持
      legacy_unspecified；不原地补写已封存版本，不改 workflow、不写线上表。
- [ ] OPS-02：统一 locale-safe 发布身份、存储和发现。范围：publish assembly、
  release metadata、RTD source/alias 与测试。相同型号/市场的两语共存；身份/path
  不一致、重复 key 和 alias 冲突 fail closed；旧链接/二维码兼容；失败不损坏原快照。
  - [x] OPS-02a locale 身份/原子装配/旧路由兼容核心：#1106 已全绿合入。
  - [ ] OPS-02b 真实出版物迁移及线上旧链接/双语并存验收；历史 en 槽位不算英语单语。
- [ ] OPS-03：从发布元数据重建目录并驱动门户。范围：catalog、portal、静态资源与测试。
  US/EU/UK，默认 EU，EU/UK 共用出版物；12 语下拉只启用实际已发布语言。
  切换保留型号与市场版本，从目标语言开头进入，不追同章节。
  - [x] OPS-03a 冻结目录分组及语言入口：#1107 已全绿合入，复用 OPS-02 身份读取器。
  - [ ] OPS-03b 真实语言出版物部署及 RTD 桌面/移动验收；本地样例不替代上线。
- [ ] OPS-04：版本发布/回滚/撤回与确认回执。范围：release staging、publish
  receipt、链接回填与测试。同版本不同内容拒绝覆盖；候选不冒充已发布；
  明确 current 指针、旧版策略与撤回记录，不以源缺席当删除。
  工作流改动待专项批准；真实 Base 写回待指定记录批准并同记录读回。
  - [x] OPS-04a 本地 Web 版本封存：#1108 已全绿合入；同版本不同内容拒绝覆盖，metadata成功后才记队列成功。
  - [ ] OPS-04b 真实版本更新/回滚/撤回与 RTD 确认回执；工作流和正式回填按操作者要求暂缓。
- [ ] OPS-05：可重复运行的覆盖/健康报告。范围：只读报告模块、测试、运行说明。
  输出型号/市场/语言/版本、断链/缺失资产/发布失败；未知写 no_data 而不是零。
  明确负责人、检查频率与故障处理方式；不默认部署常驻服务或访客跟踪。
  - [x] OPS-05a 本地冻结产物检查：#1105 已全绿合入，部署/访客状态明确 no_data。
  - [ ] OPS-05b 真实线上健康、覆盖分母、故障负责人及处理验证。
    - [x] OPS-05b1 冻结目录的有界 HTTPS HEAD 检查：#1112 已17/17全绿合入；HTTP 成功不等于版本、正文或翻译验收。
- [ ] OPS-06：反馈闭环。范围：可配置入口、上下文、处理记录和运行说明。
  入口携带型号/市场/语言/版本/页面；渠道与负责人由操作者指定。
  一条受控真实反馈完成接收→定位源→审核修复→再发布→回告，并保留证据。
  - [ ] OPS-06a 默认关闭的反馈入口与最小上下文复制能力；不启用未指定的渠道。
  - [ ] OPS-06b 操作者指定渠道/负责人后，完成受控真实反馈闭环。
- [ ] OPS-07：真实试点与交接。仅从已批准 Web 清单/已发布产品选择试点，
  完成补一语、版本更新、回滚演练、反馈闭环和线上健康报告；记录耗时/人工步骤。
  不为验收编造翻译或修改安全参数。文档同步、成本记录齐全后才可关闭总计划。

## 3. 长期运营最终硬出口（全部满足才把总 PR 转 Ready）

- [ ] 已批准代表手册能够复用骨架接入，且补语言不改型号专属 Python/CSS。
- [ ] 至少同一型号/市场两语真实独立 URL 可访问；正文、含字图语言正确；
  EU/UK 不重复发布，不覆盖同型号另一语言。
- [ ] 目录可从冻结发布快照与元数据重建；语言覆盖率有真实分母，未回稿不假报完成。
- [ ] 旧 URL/QR、产品搜索和语言下拉经过真实 RTD 桌面/移动验收。
- [ ] 版本更新、回滚与撤回有可复现证据；不误伤别的目标；线上内容与确认回执一致。
- [ ] 正式 HTML_link 仅在对应提交上线并验证后回填；获批记录同记录读回成功。
- [ ] 反馈渠道/负责人已确认，至少一条受控反馈修复并回告；缺渠道不勾选。
- [ ] 健康报告正常/故障两种场景有证据；故障负责人/处理时限明确。
- [ ] 所有实现 PR 全绿合入、无未解决评审；部署、操作说明与成本证据已汇总。

12 语内容全部齐套属于持续内容运营，不是本期能力门；跨端 IR-D01～D06 仍为长期债。
访客流量/搜索行为分析待隐私与采集方案批准；本期先做发布覆盖、健康与反馈运营，
不把没有接入的访问量显示为 0。

## 4. 并行、验证与回退

主集成窗口持有本 checklist/授权与共享文档；发布身份热点串行。
最多主窗口加两个工作窗口：Sol 处理发布/版本身份，Luna 处理隔离的报告/测试；
复杂问题先复现再决定升级，不重复让多个模型写同一模块。
每个窗口独立 worktree/分支，禁止触碰根 checkout 的 tmp/ 与他人的生成物。

验证阶梯：语法/Ruff→定向 unittest→完整 unittest→维护护栏→文档链接→
fixture build→旧冻结产物/链接兼容→真实 RTD。每次切片合入前重新对齐 main。
构建使用显式 `--data-root tests/fixtures/phase2`，不触发线上同步。
代码失败通过独立修复 PR；发布回退选择已验证不可变版本；不清空源目录试错。

自合依据：[MA-066](merge_authorizations.md)。全部检查（含非 required）成功、
无 changes-requested/未解决线程，才可按最终 head 合入。
workflow、公开 CLI、依赖、Base schema/写入、外部反馈/统计服务仍各自审批。
授权随计划推送生效；总 PR 不因需要授权入 main 而提前合入，实现 PR 可携带同一行。

## 5. Evidence ledger

| 切片 | PR / commit | 本地验证 | RTD / 业务验收 | 状态 |
| --- | --- | --- | --- | --- |
| 基线首页（既有） | #1102 / a55d666d | 前轮冻结产物 parity | build 34531930；[线上首页](https://ht-doc.readthedocs.io/) | 已交付，不代表运营闭环 |
| OPS-00 | 本总计划 PR | discovery + 文档链接检查（见 PR） | 不改变线上 | discovery 完成 |
| OPS-01a | [#1104](https://github.com/Bingboom/auto-manual/pull/1104) / `a2bda35a904b97ab36a603f508fd945335133860` | 12 定向测试；3987 全套 OK（24 skipped）；Ruff/护栏/文档链接/fixture check 通过；真实 prepared fixture 投影 17 页 | 内部 helper，无线上发布；CI 17/17，CLEAN，无评审/未解决线程 | 子切片完成，OPS-01b 未验收 |
| OPS-05a | [#1105](https://github.com/Bingboom/auto-manual/pull/1105) / `b541689ac5b2a704c7b47041370101e979c3776f` | 最终树12定向测试/完整unittest退出0；全Ruff/护栏/文档链接通过；早于最终修改/中断的测试不作证据 | 本地只读报告；CI17/17，CLEAN，无评审/未解决线程；线上健康未验收 | 子切片完成，OPS-05b 未验收 |
| OPS-02a | [#1106](https://github.com/Bingboom/auto-manual/pull/1106) / `64bd9b90b733b5c0a9f4b28102d28fc4bed4c103` | 最终树4016测试 OK（19 skipped）；Ruff/护栏/文档链接/fixture check通过；真实Sphinx与原子失败注入 | CI17/17，CLEAN，无评审/未解决线程；旧迁移一律 legacy_unspecified，未执行线上语料迁移 | 子切片完成，OPS-02b 未验收 |
| OPS-03a | [#1107](https://github.com/Bingboom/auto-manual/pull/1107) / `7ba6591cf189eecebd59a65e2f931239546d7b49` | 最终树4024测试 OK（22 skipped）；13定向测试/全Ruff/护栏/文档链接/fixture check通过；21本冻结语料66个HTML仅首页变化；本地390px及无hash语言跳转验收 | CI17/17，CLEAN，无评审/未解决线程；EN/FR是QA样例，不冒充真实出版物；未迁移语料 | 子切片完成，OPS-03b 未验收 |
| OPS-03a 部署 | #1107 → Hello-Docs `e551ee995e5e2e3a4c96747c8251ba065aeca43e` | mirror run `34746309950` success | RTD build `34532513` success；线上默认EU/20 EU产品/当前出版物可访问；发现legacy禁用语言的“未发布”措辞会误导，独立后续修正；双语真料仍未验收 | 部署有证据，不等于 OPS-03b 完成 |
| OPS-04a | [#1108](https://github.com/Bingboom/auto-manual/pull/1108) / `f695f7b2f72f870163d8030ef633e5e4f60b9c5d` | 最终树4035测试 OK（22 skipped）；21定向/全Ruff/护栏/文档链接/fixture check通过；固定输入双Sphinx 260文件哈希相同（只排除doctrees） | CI17/17，CLEAN，无评审/未解决线程；未消费真实队列/写线上表；两次review build因附件缺失在渲染前失败，不作E2E证据 | 子切片完成，OPS-04b 未验收 |
| OPS-03a 措辞跟进 | [#1109](https://github.com/Bingboom/auto-manual/pull/1109) / `4291d8f6c9fa91b989365839c2f538a33ca29b64` | 最终内容树4036测试 OK（24 skipped）；14定向/全Ruff/护栏/文档链接/fixture check通过；真实冻结语料65个正文HTML不变 | CI17/17，CLEAN，无评审/未解决线程；有legacy出版物时改为“Separate language page not verified”，不把元数据缺失说成内容未发布 | 修正已合入；不晋升任何语言身份 |
| OPS-03a 措辞部署 | #1109 → Hello-Docs `da0c02f7ae76ab9582bd2b4aaf9f5480efaf618b` | mirror run `34747579572` success | RTD build `34532682` success，API commit 与镜像一致；HTTPS 首页正文实际包含修正措辞；浏览器控制超时，未把此次 HTTP 验证当作新的视觉验收 | 已部署，不晋升语言身份 |
| OPS-06a | [#1110](https://github.com/Bingboom/auto-manual/pull/1110)，head `557f9b3a227d0449d23536136681b2d8b8f72fc1` | 4042全量测试 OK（22 skipped），Ruff/护栏/文档/fixture check通过；默认关闭时66个HTML逐字节不变 | 17/17检查成功且无评审线程后发起合并；main已出现同树squash `9a015afdbee91786feecaf44567a6ad4d7a0c86e`，但PR接口仍OPEN；不重复合并 | 等GitHub合并状态一致后勾选；真实渠道/负责人/反馈闭环仍未验收 |
| OPS-05b1 | [#1112](https://github.com/Bingboom/auto-manual/pull/1112)，merge `51791920bf5d9326f13b54c26af03cf2c1caf7d5` | 对齐#1111后的最终4065测试 OK（19 skipped）；10定向/Ruff/mypy/护栏/文档/fixture check通过；预先组合树与实际main对齐树均为`50a347256ec46d7a8c514230facbe7d96543bcbb` | 最终head `afbfa4ab` 的CI17/17，CLEAN，无评审/未解决线程，GitHub确认MERGED；21个现有出版物HEAD成功，不证明正文/资产/版本/翻译；首次CI启动失败见下方记录 | 子切片已合入；覆盖分母/负责人/处理验收仍未完成；无线上表写入 |
| OPS-01b2a | [#1113](https://github.com/Bingboom/auto-manual/pull/1113)，merge `0a910a3e065f5e1c9dafbd145114efad26a85e1d` | 最终4088测试 OK（22 skipped）；Ruff/mypy/护栏/文档链接全绿；共享EN/FR配置的FR封存至stored回归通过；冻结21出版物Sphinx对比无差异；本地review-asis+隔离fixture真实check/md/html及凭据封存、组装、stored、门户构建通过 | 最终head `0f255284` CI17/17，CLEAN，无评审/未解决线程，GitHub确认MERGED；默认review模式check已修复，后续md被fixture源与批准Overview哈希不匹配正确拦住，未产生release；review-asis HTML仍14new/1known警告。未修改批准图/门禁，无线上表写入、workflow变更或RTD发布 | 工程子切片已合入；OPS-01b2/OPS-01b及真实URL、内容/翻译验收仍未完成；历史release不回填 |
| OPS-01b1 | [#1111](https://github.com/Bingboom/auto-manual/pull/1111)，merge `d2c9c7542770cbe652d35a17b6b996764896b49d` | 最终4055测试 OK（22 skipped）；80定向/Ruff/mypy/护栏/文档/fixture check通过；review+隔离fixture/37哈希核验中立附件的EN check/md/html成功且三次投影manifest哈希相同；整本Web md通过；非Web显式语言保持原有失败基线 | CI17/17，CLEAN，无评审/未解决线程，GitHub确认MERGED；未发布RTD、未晋升single、无线上写入；HTML仍有14new/1known警告（含保修RST结构），不构成内容验收；未放宽门 | 子切片已合入；OPS-01b2及真实发布未验收 |
| OPS-01b 只读/隔离试点 | main `f695f7b2`，无实现 PR | 37个中立LCD/Symbol附件与已提交audited source manifest逐项size/SHA匹配，仅复用图标；未复制其他型号CSV；使用已提交fixture提供测试数据/composite合同；整本review-asis check/md/html均exit0 | 无线上发布；HTML有22条RST warning；显式lang=en失败于review fallback引用缺失cover-en.rst；不能声明独立单语发布已通 | 输入可构建；单语作用域接线待实施 |
| OPS-01～07 | 待实施 | 未运行 | 未验收 | 不勾选 |

每个实现 PR 回填：最终 head、merge SHA、运行命令/结果、上线 commit/build ID、
代表 URL、兼容/故障场景、耗时、人工操作、未释放审批。证据来自真实运行，不用计划代替结果。

2026-09-13 GitHub 故障记录：#1111 的 `34749353847` / `34749353850`
及 #1112 的 `34749354583` 为 `startup_failure`；#1112 预览 run
`34749354456` 的 job `103702901446` 执行步骤为空，错误注释为
“The job was not started because it repeatedly failed to be acquired (5 attempts).”
官方事件已包含 Actions 性能下降。确认是未正常启动而非测试断言失败后，
仅对上述四个 run 各重试一次；不修改 workflow，不把重试请求成功当作检查通过。


## 6. JE-1000F/EU real PDF asset intake (2026-09-13)

- [x] 操作者对具体的 1 个 PDF 来源、11 项既有定义、22 个英法整图导出物登记及法语主电源标签对应关系确认后，按 prod/bot 写业务 Base；不改正文标签、schema 或 workflow。
- [x] 从操作者 EU-UK V2.0 PDF 直接提取 55 张含字整图（5 语各 11 张），已批准配方哈希全通过；本批仅登记 EN/FR 各 11 张。
- [x] 来源 `recvv6pNQ9801w` 的 source_file 非空，回下载 SHA256 为 `0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe`。
- [x] 11 项定义复用原记录，22 项导出物逐条回读 export_file token，回下载逐字节 SHA256 验证；format=png、gate_status=approved、build_eligible=true 均读回确认。
- [x] EN overview 源绑定仅批准的 12.5→6.5 A 差异；FR 另有 Bouton POWER principal→Bouton POWER 标签差异，已确认对应关系。图片 content SHA 不变，严格源漂移门禁不变。
- [x] 本地 PDF overlay 的 EN/FR check/md 与严格 RTD Sphinx 构建通过；每语 11 张整图文件哈希一致，浏览器可见 On/Off、Marche/Arrêt 与完整引线；表格仍为 HTML。
- [x] 从线上重新 `build.py sync-data` 成功，fresh snapshot 含 38 个 Web composites（原 US 16 + EU 22）；EU 22 项均带真实 definition/export record_id 且下载哈希通过，不依赖本地 overlay。
- [x] fresh 线上快照 EN/FR 的 check、Web md、RTD source、sphinx -W 全部通过；每语 11 个整图槽位的 source/content hash 均匹配 live manifest。与 PDF-derived Markdown 字节级一致：EN SHA256 `9e9dc4ab5c35cd72a2f3ebea10858b404deff2be08a4e258d90ec52792bbc3da`；FR SHA256 `cb8c9d71a21a665435bf208c83ab3f93b5e22c4ecda4832b06c919e656dab21d`。
- [ ] 不可变双语 release、Hello-Docs 发布 PR 与 RTD 实页验收；上述入库不代表已上线，OPS-01b/02b/03b 保持未勾选。

登记陷阱：首次线上重同步拒绝缺少 format 的导出物；补齐现有 format=png 字段并逐条读回后重同步成功，未绕过门禁。阶段回执保存在操作机 `/tmp/manual-ops-live-pilot.V2B8Uy/registration-evidence/README.md` 与同目录逐记录 JSON；该本地路径不是公开线上发布证据。


### OPS-01b3 Web queue locale boundary (2026-09-13)

- [x] 单语 Web Publish 队列接入：[PR #1114](https://github.com/Bingboom/auto-manual/pull/1114) 已合入，merge `112d57aa4b74e78a7a0e744f78e9b432c169effb`，最终 head `9bc81fca4cb1a5b932c4e624a97f8e65caf5e868`。17/17 CI 成功，CLEAN，无 changes-requested/未解决讨论，包含当时最新 main `0a910a3e`，依据 MA-066 合入。
- [x] 真实 eu-en/en、eu-fr/fr 配置解析及同型号/市场/版本/ref 的两个 singleton 分组测试通过；单语 Web 必须明确 Lang，并启用语言路径和记录级分组。拒绝 merged+Lang，保留历史 blank-Lang whole-book Web 及 Print 规则。
- [x] 本地 4097 项 unittest 通过（22 skipped），51 项定向测试通过；Ruff、维护护栏、197 文档/1798 链接检查、US EN fixture build.py check、git diff --check 均通过；独立只读审查无 P1/P2。
- [x] 英法正式 Web 版本以操作者指定 PDF 发布版为准：JE-1000F EU-UK V2.0（文件日期 2026-06-18）；显示版本 V2.0，发布 Version 使用 2.0，不沿用草稿 1.0。操作者原话：「最新版本呀 就以pdf发布版为准」。
- [ ] 精确线上队列新增/武装与正式发布尚未执行；版本选择不自动释放 workflow 或线上写入门禁。

本片不修改 workflow、公开 CLI、schema 或线上数据。工作流提前 HTML_link 回填仍 deferred，镜像部署与 RTD 双语实页仍须独立验收；总计划保持 Draft。

版本依据回读（2026-09-13）：业务资产来源记录 `recvv6pNQ9801w` 的 `document_revision=V2.0`，`source_file` 非空且名称对应上述 PDF；本地 PDF SHA256 与登记值相同：`0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe`。后续版本以操作者提供或确认的 PDF 发布版为准，不从草稿号、PR 号或构建次数推断。
