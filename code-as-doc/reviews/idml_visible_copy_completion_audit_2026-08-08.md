# IDML 可见文案补全审计（2026-08-08）

## 结论

IDML 正文 renderer 只能消费和排版源文案，不能根据 reference PDF、组件类型、语言包或
内部 page role 自行补出读者可见的标题、标签、说明、时长或占位句。物理第 1–3 页
（封面、前言、目录）和封底属于批准版式例外，先保持既有装配；例外不得扩散到正文。
本轮审计确认，
当前 JE-1000F/US Key Combinations 最后一行的 `Main POWER button + LED Light
button` 来自冻结 RST，并非 renderer 拼接；该源文案应按操作者要求改为 `Power Button
+ LED Light button`。同时，IDML 实现仍有一组缺源 fallback 会在其他输入下补出可见
英文，必须一起清除并由自动门禁阻止回归。

## 审计边界

扫描面覆盖：

- `tools/idml/**/*.py`；
- `tools/idml_rst_extract.py`、`tools/idml_rst_tables.py`；
- `tools/export_idml.py`；
- production IDML 和交付包中的 `flow/manual.flow.idml`；
- JE-1000F/US 当前冻结 review、生成 draft、共享语言模板和批准 reference-layout
  合同。

以下代码常量不属于业务文案补全，允许继续由 renderer 所有：字体 fallback、段落/
对象/StoryTitle 名、资产角色、内部 page role、几何默认值、诊断信息，以及只影响排版
的真实标题匹配表。结构序号与来自源组合分隔符的 `+` 也属于 renderer 投影，不是新增
业务内容。

批准装配例外只覆盖物理第 1–3 页和封底：preface 首个无语言码 `IMPORTANT` 的 EN
徽标、TOC title / language bar 的既有 fallback、封底 region fallback 与 reference
contract 联系信息。它们由 page-role scoped composer 所有；Key Combinations、
Operation、Symbols、FCC、App 等正文组件不在例外范围内。

## 可见文案来源合同

1. 标题、表头、标签、说明、联系信息和占位句必须来自模板 RST、冻结 review、源表、
   配置或显式 `manual-ir` / ComponentSpec payload。
2. renderer 可以按稳定结构拆分、重排和映射角色；由源动作句提取 `3 seconds` 并紧凑
   显示为 `3s` 也允许，但匹配失败不得补默认值。
3. source-required 字段在批准 production 路径缺失时必须 fail-closed；兼容/设计手递路径
   最多静默省略该可见层，不能显示内部 `kind` 或英文占位句。
4. language registry 可以用于识别、路由和排版校准，不能替代当前页面已提供的真实标题、
   表头或 warning label。

## 确认问题与修复归属

| 类别 | 当前补全 | 正确来源 / 修复 |
|---|---|---|
| 未知组件 | `flow_idml._component_fallback_text()` 最后显示 `kind` / `component` | 只保留 payload 的 `label` / `texts`；均为空则无可见文本 |
| reference figure | 缺 copy 时显示 `Editable reference figure` | 只显示源字段；严格模式缺语义失败，兼容模式为空 |
| operation duration | 匹配不到动作句时补 `3s`；renderer 再补 `On/Off` / `3s` | duration 只从动作句提取；`On/Off` 进入显式源 payload |
| LED operation | renderer 直接写死 `SOS` | `SOS` 进入显式源 payload，不从模板图猜词 |
| 数据页标题 | 缺 H1 时补 `SPECIFICATIONS`、`LCD DISPLAY`、`MEANING OF SYMBOLS` | Manual IR 中的真实 H1 / spec start title 必填 |
| TOC | 缺 `HBTocTitle` 时补 `TABLE OF CONTENTS`；数据页 TOC 标题曾来自 renderer registry | 第 3 页保留既有 TOC fallback；正文页面标题仍必须来自真实 H1 |
| Symbols | 标题、表头和 warning label 从 language registry 补出 | `SymbolPageData` 保留 H1、两组源表头和源 signal label |
| Safety / Maintenance | 缺标题时补 page stem、`OPERATING INSTRUCTIONS`、`USER MAINTENANCE INSTRUCTIONS` | safety / maintenance RST 的显式 H1/H2 必填 |
| 封底 | Python `_BACK_COVER_COPY` 与 reference plan 的 `display_address`、`phone_suffix`、`contact_lines` | 批准封底例外，保持既有 region / reference-contract 装配 |
| data story API | 默认或写死 LCD/spec/symbol/troubleshooting 标题 | 调用方必须传源标题/表头，API 不提供业务 copy 默认值 |
| flow hand递件 | phase2 fallback 补英文标题/表头，组件缺 label 时用 `variant.upper()` | 直接投影 prepared RST 的 data/component payload；无源表头不新增可见表头 |
| FCC | extractor 为 `HBFccBlock` 合成可见 `FCC` H1 | 只输出源 FCC component；Web 的导航 H1由 Web 源分支所有 |
| App inline | `Click the **Add device** button` 被重写为新的英文句子 | regex capture 原样复用源 prefix/button/suffix，只插入图标 marker |
| Preface 标签 | flattened `**IMPORTANT**` 缺语言码时补 `EN` | 批准第 2 页例外，保持既有徽标装配 |
| flow notice | 缺 label 时按 fence kind 补 `WARNING` / `NOTE` 等 | fence 只传源 label；缺失交给 source-required 门禁失败 |
| flow 图片 alt | 从文件名派生 alt，空值再补 `figure` | 无源 alt 时保持空 alt，不把资产路径变成读者文案 |
| 死文案注册表 | `SYMBOL_COPY` 曾留在 IDML facade；TOC language pack 属第 3 页装配例外 | 删除正文 `SYMBOL_COPY`；TOC registry 只允许 page_toc 消费，不得提供正文标题 |
| Symbols 续页 | FCC 续页只有行数据，renderer 有机会自行选择表头 | `SymbolOverflow` 同时携带源行与源 `icon_headers` |

## 安全网与实施顺序

1. 增加行为测试：每个缺源入口都不得输出已知占位文案、内部 kind 或默认英文标题；批准
   production 路径验证 fail-closed。
2. 增加静态门禁：IDML 可见文本 sink 不接受业务字符串 literal；允许名单只覆盖结构性
   `+` 和明确的样式/StoryTitle 参数。
3. 修改共享模板、冻结 review 和生成 draft；保持三者在本目标上的显式内容一致。
4. 更新 reference-layout content identity 与受影响 page digest，但保持 52 个 source
   binding、58 个物理页、source 顺序、language、page role、composition map、flow split、
   reference PDF identity 全部不变。
5. 按 Ruff → 定向测试 → 全量 unittest → maintainability / doc / reference pin → 真实
   JE-1000F/US build → InDesign 预检和重点页视觉检查的顺序验收。

## 扫描结果

本轮对 `tools/idml/**/*.py`、IDML extractor、`export_idml.py` 和 flow handoff 做了三层
扫描：已知标题/标签 literal、`.get(..., "copy")` / `or "copy"` fallback，以及 AST 中
进入可见文本 sink 的字符串。剩余英文 literal 均已逐项归类为 StoryTitle/样式名、诊断、
资产角色、几何校准键、源文本识别键或第 1–3 页/封底批准装配例外；它们不在正文新增
业务文案。flow notice、flow alt 和正文死 registry 问题已经纳入静态回归门禁。

## 最终生产验收

最终 JE-1000F/US production build 继续满足批准装配边界：52/52 source matched、
58 个物理页、663 个 story、573 个 Manual IR block、`skipped_raw=0`。解包最终 IDML
后扫描全部 2423 个可见 `Content` 节点（108265 个字符），`Main POWER`、
`Editable reference figure` 和内部 component kind 均为 0 命中；Key Combinations 的
按钮标签来自冻结 RST / Manual IR，最终页面使用 `Power Button` 与
`LED Light button`，不是 renderer 补词。

InDesign 原生预检结果为 58 页、overset 0、missing fonts 0、bad links 0；PDF/X-4
输出合同同时通过 subtype、`Japan Color 2001 Coated` output intent 和 `JC200103`
condition 三项检查。逐页 PDF/X 探测曾将唯一缺字定位到物理第 54 页西语规格表的源
文案 `Nº de modelo`：production Gilroy 缺少 `º` 字形。修复保留源文案不变，仅将该
字符路由到已登记的 Arial Unicode MS 字体 fallback；这属于外观/字体投影，不属于
业务文案补全。修复后全 58 页 PDF/X 导出无警告，并完成全页 contact-sheet 与第 54 页
原尺寸视觉检查。

## 非目标

- 不把字体、样式名、几何 token 或资产角色迁移到内容源；
- 不迁移所有 language registry；仅禁止它替代已存在的出版文案；
- 不改变 reference PDF、固定分页、composition map 或页面视觉目标；
- 不修改、提交或删除 `tmp/`、PDF、IDML、INDD 和其他构建产物。
