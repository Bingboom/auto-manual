# 七本日语存量说明书 Web 候选（2026-11-12）

Status: active

## 范围与来源

操作者指定物料转换为日语网页版并要求3个并行agent；随后明确JS-40A只选000464，000348不作为交付版本。最终为7本、7个产品身份。

沿用[项目定位§5.1](../architecture/Hello_Docs_Positioning.md#51-网页说明书的三条路线)的存量PDF/AI接入路线和[Web发布契约](../dev/web_publish_pipeline/input-paths.md)。来源是发布文档管理「说明书转网页」表JP记录中当前「竖版说明书」附件；原件逐一下载并锁定字节数/SHA-256。原稿全部转曲，正文按页转录、日语OCR交叉检查与视觉核对，原稿是事实依据。

当前状态为`review-candidate-no-release-authorization`、`publication_eligible=false`。工程PR供审阅；接受原稿与像素后再封存发布凭据、提交Hello-Docs发布PR及核验RTD。

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

最终全量单测使用Python3.12.13和`requirements.lock`：6257项，0失败、0错误，92项按条件跳过。七包在同一环境独立重建，IR/MyST/素材逐字节一致，冷回放及素材/CSS篡改拒绝、严格Sphinx全部通过；最终HTML与已核验的1280/390页面字节一致。四处回收图均与公共canonical文件逐字节一致，并验证真实透明通道。Shell子进程的PATH指向同一Python环境，本机HTTP用例在允许loopback的环境执行。

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
