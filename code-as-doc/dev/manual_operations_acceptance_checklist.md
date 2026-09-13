# Manual Operations Acceptance Checklist

Status: active / umbrella PR stays **Draft**. Updated: 2026-09-12.

唯一合并条件：**实现 manual 运营的打通**。建好首页、代码合入、CI 绿或生成
本地样例均不等于闭环验收。每完成一个独立切片，开实现 PR；合入并完成该切片
验收后，才在本文件勾选并登记 PR、commit、命令结果和部署证据。

## 1. 边界与 discovery

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

## 2. 实现切片与验收

- [x] OPS-00：完成发布身份/回填顺序/门户基线 discovery，登记独立授权 MA-066。
- [ ] OPS-01：复用现有单语投影，确认可用语言来自实际冻结内容，缺译失败或明确不可用；
  不把混合语全文标为单语。范围：语言 bundle/helper 与测试；不引入 Chrome/PDF 依赖。
- [ ] OPS-02：统一 locale-safe 发布身份、存储和发现。范围：publish assembly、
  release metadata、RTD source/alias 与测试。相同型号/市场的两语共存；身份/path
  不一致、重复 key 和 alias 冲突 fail closed；旧链接/二维码兼容；失败不损坏原快照。
- [ ] OPS-03：从发布元数据重建目录并驱动门户。范围：catalog、portal、静态资源与测试。
  US/EU/UK，默认 EU，EU/UK 共用出版物；12 语下拉只启用实际已发布语言。
  切换保留型号与市场版本，从目标语言开头进入，不追同章节。
- [ ] OPS-04：版本发布/回滚/撤回与确认回执。范围：release staging、publish
  receipt、链接回填与测试。同版本不同内容拒绝覆盖；候选不冒充已发布；
  明确 current 指针、旧版策略与撤回记录，不以源缺席当删除。
  工作流改动待专项批准；真实 Base 写回待指定记录批准并同记录读回。
- [ ] OPS-05：可重复运行的覆盖/健康报告。范围：只读报告模块、测试、运行说明。
  输出型号/市场/语言/版本、断链/缺失资产/发布失败；未知写 no_data 而不是零。
  明确负责人、检查频率与故障处理方式；不默认部署常驻服务或访客跟踪。
- [ ] OPS-06：反馈闭环。范围：可配置入口、上下文、处理记录和运行说明。
  入口携带型号/市场/语言/版本/页面；渠道与负责人由操作者指定。
  一条受控真实反馈完成接收→定位源→审核修复→再发布→回告，并保留证据。
- [ ] OPS-07：真实试点与交接。仅从已批准 Web 清单/已发布产品选择试点，
  完成补一语、版本更新、回滚演练、反馈闭环和线上健康报告；记录耗时/人工步骤。
  不为验收编造翻译或修改安全参数。文档同步、成本记录齐全后才可关闭总计划。

## 3. 最终硬出口（全部满足才把总 PR 转 Ready）

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
| OPS-01～07 | 待实施 | 未运行 | 未验收 | 不勾选 |

每个实现 PR 回填：最终 head、merge SHA、运行命令/结果、上线 commit/build ID、
代表 URL、兼容/故障场景、耗时、人工操作、未释放审批。证据来自真实运行，不用计划代替结果。
