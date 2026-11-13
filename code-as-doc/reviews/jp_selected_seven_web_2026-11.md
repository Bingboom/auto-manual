# 七本日语存量说明书 Web 审核与发布（2026-11-12）

Status: active

## 范围与来源

操作者指定物料转换为日语网页版并要求3个并行agent；随后明确JS-40A只选000464，000348不作为交付版本。最终为7本、7个产品身份。

沿用[项目定位§5.1](../architecture/Hello_Docs_Positioning.md#51-网页说明书的三条路线)的存量PDF/AI接入路线和[Web发布契约](../dev/web_publish_pipeline/input-paths.md)。来源是发布文档管理「说明书转网页」表JP记录中当前「竖版说明书」附件；原件逐一下载并锁定字节数/SHA-256。原稿全部转曲，正文按页转录、日语OCR交叉检查与视觉核对，原稿是事实依据。

原候选保持`review-candidate-no-release-authorization`、`publication_eligible=false`。操作者在本会话明确要求「审核一下 然后合入 上线发布文档」，授权登记为MA-433；经独立复现与来源复核后，另建同名加`-release`的批准快照，最终合入后在真实Git提交上封存凭据、提交Hello-Docs发布PR并核验RTD。该授权委托agent审核后发布，不声称操作者另做过逐像素验收。

| 物料 | 印刷身份/标题 | 原稿页数 | 冻结源候选 |
| --- | --- | --- | --- |
| 38-0001-000512 | JSG-0304B · Jackery Solar Generator 300 Plus 40W Mini | 20 | [源包](../../manual_sources/JSG-0304B/JP/ja/git-20261112-fe9f1b56-m000512/README.md) · [来源/输入哈希](../../manual_sources/JSG-0304B/JP/ja/git-20261112-fe9f1b56-m000512/source_manifest.json) |
| 38-0001-000491 | JSG-2404A · Jackery Solar Generator 240 40W Mini | 20 | [源包](../../manual_sources/JSG-2404A/JP/ja/git-20261112-e59cc1bc-m000491/README.md) · [来源/输入哈希](../../manual_sources/JSG-2404A/JP/ja/git-20261112-e59cc1bc-m000491/source_manifest.json) |
| 38-0001-000464 | JS-40A · SolarSaga 40 Mini later multilingual source: Japanese projection only | 28 | [源包](../../manual_sources/JS-40A/JP/ja/git-20261112-1a96bf34-m000464/README.md) · [来源/输入哈希](../../manual_sources/JS-40A/JP/ja/git-20261112-1a96bf34-m000464/source_manifest.json) |
| 38-0001-000034 | PTB021 · Jackery ポータブル電源 240 | 12 | [源包](../../manual_sources/PTB021/JP/ja/git-20261112-c1f0f04e-material-web/README.md) · [来源/输入哈希](../../manual_sources/PTB021/JP/ja/git-20261112-c1f0f04e-material-web/source_manifest.json) |
| 38-0001-000035 | PTB041 · Jackery ポータブル電源 400 | 12 | [源包](../../manual_sources/PTB041/JP/ja/git-20261112-1fc3e6ff-material-web/README.md) · [来源/输入哈希](../../manual_sources/PTB041/JP/ja/git-20261112-1fc3e6ff-material-web/source_manifest.json) |
| 38-0001-000036 | PTB071 · Jackery ポータブル電源 708 | 12 | [源包](../../manual_sources/PTB071/JP/ja/git-20261112-ab6bd123-material-web/README.md) · [来源/输入哈希](../../manual_sources/PTB071/JP/ja/git-20261112-ab6bd123-material-web/source_manifest.json) |
| 38-0001-000027 | BN-RB15 · JVC ポータブル電源 BN-RB15 | 16 | [源包](../../manual_sources/BN-RB15/JP/ja/git-20261112-f2421529-material-web/README.md) · [来源/输入哈希](../../manual_sources/BN-RB15/JP/ja/git-20261112-f2421529-material-web/source_manifest.json) |

技术快照日期/哈希标识转换输入，印刷版号未知的继续记为null。JVC正文按封面印刷型名BN-RB15，文件变体BN-RB15-C只记录在来源身份。

## 原文与共享呈现

- 七本均经现有public Manual IR / prepared-document入口生成ComponentSpec、MyST和HTML，复用共享主题。新增源包自带可重放适配和源输入清单，不新增逐型号配置或phase2印刷目标。
- 同梱品、LCD、符号、规格、安全提示、保修、参考图按各包`component_map`进入对应共享组件。原稿中不能由共享组件表达的多列目录/保証書表，逐表登记`shared_component_exceptions`与理由；没有包内配色、边框或ht-*仿排。
- 原生段落、列表、参数表可选择/检索；插图先盘点同型号和共享资产，再按已记录的身份/字节哈希复用。确有源图差异时由asset-intake裁取，图内引线、手指、袋绳、二维码四边及手机截图整框保留。
- PTB三本及JVC的独立回收标志，按操作者「复用啊」的明确决定统一复用公共库`li-ion/recycle-li-ion`标准图，文件逐字节相同。原印`Li-ion 20`与公共图的差异记入来源和审查记录；不再为四本保留独立提取的生产SVG。
- 印刷logo、封面产品图、页码和目录的Web省略单独记录；欢迎、适用范围、支持链接、商标、免责、FAQ、保证书等实质文案继续保留。
- 000464仅投影公共指南物理3–5、日语25–27及共同联系页28；其余语言与印刷目录列明排除。五张展开图的真实348图稿作为包内donor输入并与464原图对照，只用于可复现图稿；正文和参数依据464，交付目录中没有348的Web版本。

## 逐页复核要点

- 同名SolarSaga40Mini也有来源版次差异：512套装保留其970*300*2.5mm，491套装及独立464保留各自1020*300*18.5mm。独立版本选择不改写套装已印事实。
- 套装省エネ表、40°C风险段落、免责与App逐段对原稿核对；491表三行ON与原拼写dispaly保留，参考中的UPS20ms、600Plus手柄条与多余機器共有句不进入当前原稿。套装第5步必须是其自身带手柄电源图，不能复用无手柄设备的独立太阳能说明书末图。
- PTB三本分别核对容量、接口、运行/充电时间和FAQ差异；PTB071曾被OCR拆乱的p6按原图重录。源稿重复字、重复透传段与温标疑点保留并列在各包source_concerns，不作为转换时的技术纠正。
- JVC保留JIS说明、FAQ/注册/在线说明书入口、商标、保修与售后、末页空白保証書；图示只使用本机原稿。
- 三个agent独立worktree制作（套装2本、太阳能1本、旧款电源4本），根窗口做来源锁定/独立重建/参数抽检/整合；太阳能agent额外只读交叉复核491全文及JVC关键页。

## 验证与审阅入口

各包`evidence/`保存逐页映射、文字/参数复核、资产复现和篡改拒绝、冷回放、严格Sphinx及1280/390浏览器证据。审阅页面把原PDF、候选和共享参考版并列。参考JE-300B/JE-240A/JE-300C取自Hello-Docs提交`4fff0818de768039dbe972cb077d801c46e73c1c`冻结发布源，127个文件按发布清单哈希核对；太阳能对照JS-100I JP共享版。参考用于组件与呈现，源稿决定文字和事实。

候选提交`6abe1128`的制作阶段全量单测使用Python3.12.13和`requirements.lock`：6257项，0失败、0错误，92项按条件跳过。七包在同一环境独立重建，IR/MyST/素材逐字节一致，冷回放及素材/CSS篡改拒绝、严格Sphinx全部通过；最终HTML与已核验的1280/390页面字节一致。四处回收图均与公共canonical文件逐字节一致，并验证真实透明通道。Shell子进程的PATH指向同一Python环境，本机HTTP用例在允许loopback的环境执行。

CI首次扫描的12处匹配逐项核对为当前附件的`file_token` / `source_file_token`资源ID；原字段和值保留。扫描配置为这两个精确键增加独立完整行规则，限定20–32位字母数字和单独字段行；认证字段、附加后缀字段、长度边界以及资源ID与凭据同行的紧凑JSON，以实际Gitleaks负对照核验，整棵提交树按CI相同版本扫描。

本批回归入口：

```bash
python -m ruff check build.py integrations tools tests scripts
python -m unittest
python -m tools.web.frozen_package_registry check
python -m tools.check_maintainability_guardrails
python -m tools.check_doc_link_integrity
python build.py check --config configs/config.ja.yaml --model JE-1000F --region JP \
  --data-root tests/fixtures/phase2 --staging-root <isolated-output>
```

最后一项仅是既有日规产线的fixture回归，不验证七本外部正文；正文由各包输入检查、转录核对、独立冷重建、共享样式准入、`sphinx -n -W --keep-going`及浏览器核验覆盖。`tests/test_selected_japanese_material_web.py`单独锁定七个附件身份、JS-40A选择、套装关键差异及回收标志公共图字节绑定，防止同名规格/参考文案串入和重复提图。

首次额外基线在缺少本地phase2快照时失败，已按本次缺失路径恢复生成目录，随后以测试快照和隔离输出通过；未更改产品快照或放宽门禁。分支wrapper因另一窗口占用main而拒绝切换，保留失败后从干净、与origin/main一致的隔离checkout创建功能分支，不触碰外部main。

## 本次独立审核与发布修复

审核起点为PR #1712的`6abe1128c27a186228185390d26f87adc9d3e2c9`。七个适配器在隔离目录独立生成的IR/MyST/素材均与候选逐字节一致，严格Sphinx通过；附件身份、原始SHA-256、页数、套装与独立版尺寸差异及回收图复用通过定向测试。原候选、原PDF、全部来源疑点继续保留。

正式封存检查发现旧款电源四包缺少符号表的原稿来源绑定，批准快照补齐物理页、图形索引、图形/说明/行矩形及说明像素SHA-256，逐行调用既有`require_symbol_asset_admission`，不放宽固定阈值、不新增豁免。

| 目标 | 原候选问题 | 发布修复与来源 |
| --- | --- | --- |
| PTB021 / PTB041 / PTB071 | 缺6行来源绑定，部分旧图标未通过正式源图比较 | 禁止拆解改复用现有`native/je1000d-jp-00c43a89-02`（PTB021误差0.009126，低于0.02）；防水/湿手复用既有已确认canonical。原稿重复字继续保留，6行实际图形和说明均绑定原PDF物理第7页。 |
| BN-RB15 | 缺来源绑定；原稿“実行”行含指示与拔插头两图，候选漏后一图；现有共用图与本机原印图形不在固定误差内 | 补回拔插头图，共3行绑定物理第4页。先盘点并比较既有共用图；无合格图后，将本机三枚原生矢量按来源哈希登记为独立variant并逐字节复用，既有图标、canonical选择、说明别名及准入规则保持不变；三枚新variant仅作为对应已有语义组的非标准来源变体登记。 |

逐文件差异在每个发布包的`source/reviewed-candidate.json`，授权与原稿/候选哈希在`source/approval.json`。JSG两包和JS-40A的Web树仅IR授权元数据改变；PTB另有3枚共享图标替换；JVC另有3枚图标、补图后的MyST及相应IR引用/内容哈希变化。日语文字与技术事实不改写。

自动审批曾拒绝扩展全局canonical说明别名，原因是影响其它项目；该方案未落地。最终采用上述来源限定的既有variant/原生variant方案，并通过审批。共享库增量仅为3条BN-RB15素材及其文件、对应既有语义组的variant成员登记，历史冻结包按既有登记规则保持冻结。

发布快照本地验证：6项定向测试、Ruff、维护性门禁、文档链接检查、239包冻结登记和既有JP fixture回归通过。七份最终发布Web均通过严格Sphinx及1280/390浏览器检查，零图片丢失、脚本/资源错误和横向溢出；Gitleaks8.30.1整树脱敏扫描通过。完整CI在最终head上全部适用项通过后才合入。

最终head首次完整CI运行6259项，仅共用符号目录“每个variant恰好属于一个组”的完整性测试失败（3枚JVC新variant未分组）。已补充对应组的非标准来源变体登记，不改canonical、caption、decision或固定误差；定向覆盖后重跑完整CI，失败未作为可合入状态。

真实发布预检又确认两项发布必需修复：组装器原本未复制已封存的`shared-style-admission.json`，现将此已知审核sidecar逐字节保留，并扩展整包清单回归；210份既有源包自身证据全部核验通过。七份新增后共217个目标，冻结预检源库为1,613,577,831字节，原1536MiB预算不足。仅将独立冻结源存储预算设为1600MiB，保留768MiB网页/网络预算、20,000源文件、10,000输出文件、32MiB单文件及所有来源/路径/哈希检查。conf.py保持业务main一致；生成CSS仅带入本批所需、已在工程main批准的新选择器。旧210份源稿均未使用这些选择器，全部旧规则保留。

操作者随后明确「先不分类写入」，并选择「按其他说明书继续上线（推荐）」。因此所有线上Base、分类、项目号、网页记录和链接字段保持原样；本批七个型号在目录与产品矩阵显示于“其他说明书/其他”。整站`Sphinx -W`生成全部217目标，仅报8条已接受的分类警告；这不表述为无警告通过，也不豁免其它错误。正常生产构建、来源/资源哈希、单目标严格Sphinx、桌面/手机核验及全部适用CI仍须通过。

整站手机端检查还定位到JVC保証書原生表在390px视口展开为592px。发布版仅用既有`table-wrapper docutils`容器包裹原表，使横向滚动限制在表格面板；日语文字、空白填写栏、原生表格和其它页面不变，改动记录于`source/release-layout-review.json`。
