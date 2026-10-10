# Build guide: per-target Web source notes

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

### JE-100C/EU nine-language Web source

JE-100C/EU has authored Web sources for `en/fr/es/de/it/uk/pt/nl/pl`. Use the
EU language-family config (`config.eu-<lang>.yaml`) with the matching `--lang`.
The model identity snapshot remains shared at
`manual_sources/JE-100C/EU/en/2.0/phase2`; localized copy lives in each
`docs/templates/page_je100c_eu-<lang>/` and is source/hash bound by that locale's
`manual_sources/JE-100C/EU/<lang>/2.0/source_manifest.json`.

```bash
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web \
python3 build.py md --config configs/config.eu-fr.yaml \
  --model JE-100C --region EU --lang fr \
  --data-root manual_sources/JE-100C/EU/en/2.0/phase2 \
  --staging-root reports/je100c-web-fr --no-clean --skip-root-index
python3 -m sphinx -b html -W --keep-going -D language=fr \
  reports/je100c-web-fr/docs/_build/JE-100C/EU/fr/md \
  reports/je100c-web-fr/preview
```

French, Spanish, German and Italian use the newer operator-supplied PDF. The
Ukrainian, Portuguese, Dutch and Polish AI sources are aligned to its English
revision under the operator's explicit instruction; `newer_english_alignment.json`
records USB-C charging, car overheating wording, cycle-life, chemistry and
battery-disposal deltas and their translation-memory/source evidence. This
is local candidate intake, not a new source-table approval or publication.

`pt` is distinct from `pt-BR`; its live TM field is `eu-pt`. The central
language registry enables authored Web routes for pt/nl/pl without claiming
provisioned phase2 core-table columns or a governed IDML language pack.
The language-family configs presently onboard JE-100C only for those three
new locales. No live Base schema or records are changed by this build.

Authored signal-word rows may declare `hb-signal-warning`,
`hb-signal-caution`, `hb-signal-note`, or `hb-signal-tip` RST roles on their
labels. These roles retain the source's warning-triangle semantics independently
of whether the displayed label is in a shared translation fixture. Conflicting
roles fail; existing unmarked sources retain label-based recognition.

Authored-only Web locales retain the shared `content-lint` column fallbacks for
local snapshots without enabling live synchronization or IDML support. For
JE-100C, whose localized copy is authored RST rather than core phase2 columns,
verify the source-bound RST, asset hashes, builds and rendered pages directly;
an empty source-table observation is not a localized-copy audit.

### 原生 PDF 的已确认勘误

原生语言导入的 `source/errata.json` 可为已确认条目登记 `native_bindings`：源哈希、确认记录、来源页码、精确字段路径以及修改前后全文。适配器在共享组件构造前应用，原始提取证据保留；原文或来源不匹配即失败。文字勘误涉及带标注的概览图时，须同时修正图内文字并重锁资产哈希；清空待确认状态不能代替实际修正。

冻结 PDF 参数表的语义换行由 `source/target_layout.json` 各语言的 `specifications.value_breaks` 声明（`group`、从零开始的 `row`、唯一匹配的 `before`）。例如车充／PV 共用单元格在 `PV:` 前换行；源文字和已批准勘误先保持完整匹配，再投影为共享 IR 的 `line_break`，不恢复印刷版所有折行、不拆出额外表格行。更新时创建新的冻结版本，旧版本保持不变。

HTP011 英文无图标 LCD 说明通过共享 `lcd_descriptions_template.rst` 显式绑定
`HB-TABLE-REFERENCE/lcd-descriptions`，保留名称／说明两列及原稿文字；
发布封存直接校验组件，不再依赖该目标旧 LCD 表的内容哈希例外。

Intake preparation: [source-copy work packets and shared-art review](../dev/manual_intake_assistance.md) enumerate pending work without approving a baseline or publishing.

共用图确认清单可通过 `tools.manual_intake_assist art-review --selections` 导入；
太阳能保留型号/数量标识，车充文字用 HTML/CSS，操作与按键图片不纳入共用库。
图标按原稿中匹配的符号复用，独立图标须真实透明底。

### FridgeGuard US English Git-only input

The user-supplied JE-1000E-SIL / US / en Illustrator master is frozen with its
structured specifications and source hashes. Use the existing US English family
with the explicit data root; no online Base write or queue row is required.
See [source and acceptance record](../reviews/je1000e_sil_us_en_web_intake.md)
for the exact command and retained source errata.

Web symbol legends use warning triangles for WARNING/CAUTION; NOTE/TIP remain text-only badges, using the shared localized signal-word classification.

FCC binding is content-driven for every model and region: an exact FCC heading, `hb-source-fcc` declaration, or governed FCC source filename requires `HB-SPECIAL-FCC`. A Part 15 opening declares only a headingless orphan fragment; compact statements on mixed pages with other headings remain native source content. Whole-document source assembly rejects a missing or duplicate FCC claim; completed-IR rendering and legacy fragment rendering reject absent FCC output. The existing parser still requires the opening, localized column split, measures and modification copy. Unsupported or incomplete source structure fails with its source path; it never falls back to plain text. New targets need no model allowlist or per-model FCC configuration.

LCD icon tables use the shared `HB-TABLE-LCD-ICON` four-column component. An authored `hb-lcd-icon-table` may opt into `hb-lcd-merge-number` and `hb-lcd-merge-description`: only adjacent identical number cells, or descriptions within the same number group, merge in Web output. Keep separate semantic source rows and real icon assets; do not substitute the three-column `hb-source-lcd-legend` when the source includes an icon column.

Declare a standalone LCD on/off matrix with `hb-source-lcd-mode` on its source table to bind `HB-TABLE-LCD-MODE` without activating unrelated legacy operation tables. The source contains one artwork spanning six rows and two mode groups of three actions. Use `hb-lcd-mode-portrait` for narrow, tall device artwork; the shared component then reserves three quarters of the desktop row for the table and stacks at the existing mobile breakpoint.

For source-authored grey prose/list panels, use `figure.hb-text-panel`. It shares the existing grey rounded-panel styling and survives Web Markdown conversion. Preserve source lists rather than inventing table headers.

For a standalone App download QR, declare `img.hb-source-app-qr` followed by its adjacent text-only paragraph. It binds the existing `download-qr-only` App component for any source filename, preserving copy and the shared 9rem desktop / 6rem narrow-mobile QR size. Missing copy is rejected rather than rendered as a full-width illustration.

With store badges plus a QR in the source, declare `img.hb-source-app-download` with `data-app-download` artwork bindings for `store` and `qr`, followed by the two native copy paragraphs. It binds the existing `HB-SPECIAL-APP/download` component through public IR, without a model allowlist. Reuse the approved badges and exact source QR; missing artwork or a missing native column fails intake. Use `download-qr-only` only when the source itself has no store badges. Complete two-phone / three-phone panels reuse `hb-app-add-device-phone-art` with `hb-app-phone-pair` / `hb-app-phone-trio` display variants (22rem / 36.75rem maxima, shrinking to the available width). These shared classes retain the approved display size after finished-art replacement; plain RST width hints are otherwise normalized to the Web reading width. Keep phone borders, status/footer UI and embedded step captions intact, and inherit the same component/size choices in later locales.

To separate operation copy from artwork, an `img.hb-source-operation` can declare the existing base-art operation presentation in its `data-operation` JSON attribute, followed by the native step/supporting line block. The declaration is frozen with the Operation ComponentSpec for replay without model admission. Optional `base_art_layout.supporting_anchor` contains x/y/width percentages for separate CSS speech panels; narrow screens place their text in normal flow. Preserve the source artwork hash and exact wording.

For source-bound illustration labels, `img.hb-source-reference` with `data-reference` JSON and an adjacent line block binds the existing reference ComponentSpec and base-art renderer. Keep textless artwork out of finished-panel replacement bindings: those add finished-image attributes after source hashing. The artwork is packaged by its component asset role; its anchors and source hash remain in the IR.

Figure coverage checks resolve source-declared reference artwork hashes from the frozen page ComponentSpec before falling back to a global profile entry. Missing, duplicate or invalid declared evidence still fails; the measured hash must match the packaged artwork.

### FridgeGuard US native FR/ES local candidate

French and Spanish use `configs/config.us-fr.yaml` / `configs/config.us-es.yaml`, target `JE-1000E-SIL`, region `US`. Their Git-only data roots are `data/manual_sources/JE-1000E-SIL/US/<lang>/git-20261002-537939d0/phase2`; edit the corresponding `docs/templates/page_fridgeguard/<lang>/` source. Build with `build.py md --lang <lang> --data-root <data-root> --staging-root <isolated-output> --skip-root-index`. Native source discrepancies and asset reuse are recorded in [the intake review](../reviews/je1000e_sil_us_fr_es_web_intake.md). Publication resumed under the operator’s 2026-10-03 “推上去 发布” authorization; release acceptance is tracked in the intake review.

Frozen Web heading inline spans remain inside MyST titles, including the shared
`hb-sold-separately` badge; use shared `h3.hb-heading-label-pair` when the native small title and availability badge have separate capsule backgrounds. Verify both the heading and its navigation link after
assembly. Key combinations use `HB-TABLE-KEY-COMBINATIONS`, with authored button
pairs and shared hold-duration clocks. Match product markings before choosing
a shared button variant; function names alone do not establish artwork reuse.


新增 Web 底图的独立说明框必须与说明文字一起移除，由共享 CSS 绘制；复用旧图也需先检查裸底图。新冻结候选封装会检查已声明 ReferenceFigure 填充文字框区域的底图哈希和真实像素，拒绝残留的对比色空框；同色、仅轮廓或未声明框仍须视觉核验。完整面板、产品表面与 App UI 按角色保留。详见[共用取图规范](../../docs/renderers/contracts/STYLE_DEFINITION.md#共用图标优先web-插图选材规则)。

原稿标题条内型号使用共享 `hb-heading-model`，整行图标警告使用
`HB-CALLOUT-STRIP/warning` 的 `hb-source-warning-lockup` 声明；图内说明通过
ReferenceFigure 源坐标保留在图内，不能移为图后段落。具体样式声明见
[原稿标题型号与完整警告框](../../docs/renderers/contracts/STYLE_DEFINITION.md#原稿标题型号与完整警告框)。

Git-only 原稿的成组 PACKAGE LIST 可通过现有 Manual Flow 的 container/list/image/paragraph 表达，使用共享 `hb-package-panel` 样式绘制完整外框、原生配件名称和 availability capsule。先复用已核对配件图；冻结副本必须与记录的共用源 hash 一致。旧整图标记 `superseded-do-not-reuse`，不参与当前原稿图片覆盖；微型文档封面替换为共用文档图标时单独记录 illustration-only omission，并保留原生配件名称。

原稿中的独立深色胶囊正文提示可用 `p.hb-prose-pill > strong` 冻结到 Manual Flow；保留完整原文并拆成独立段落，共享 CSS 负责圆角、字色和窄屏换行。

图内说明使用现有 ReferenceFigure 的 `base-art-live-copy` 和来源坐标；保留底图原字节，去掉图外重复段落。完整有框插图可套 `hb-reference-contained-copy`，在手机上保留同一图框内的可读文字。

FCC Web 正文左右高度明显失衡时，可在现有 FCC 组件外声明共享 `hb-fcc-balanced-flow` 容器。桌面使用自动平衡的两栏文字流，FCC 标志左浮动并允许文字在其下方续排；手机回到单栏。DOM 保持开场、NOTE 正文、措施列表和 MODIFICATION 的原文顺序；不改 ComponentSpec 的印刷分栏点，也不按机型复制 renderer。

JA-AD600A/EU 英文的五张说明图已分离需要翻译的文字，采用共用底图加原生标签；尺寸、单位、固定铭刻和 A–F 对应编号保留。各语替换文字时复用同一底图，详见[共用底图复核](../../docs/renderers/contracts/STYLE_DEFINITION.md#ja-ad600a-eu-共用底图复核)。

仅含一段声明的 FCC 可用 `hb-fcc-composition hb-fcc-statement` 复用完整 FCC 的浅灰圆角面板和紧凑正文，保持单栏和原稿内容；完整 FCC 的 NOTE / MODIFICATION 不应补入短声明。原生 H2 标题保留在 section 中，正文和左侧共用 FCC 标志由既有受保护 figure 通过原生 flow 输出；共享 CSS 将它们排在同一面板中。


短版 FCC 的标题/正文/标志排版由共享 `web_fcc_statement.css` 承载，接入既有样式组装列表；完整 FCC 样式保持原模块，不提高维护性行数上限。

JBP-3600A EU 九语产品概览复用已审图稿，正视图和左视图分别沿用英语版的 25rem、34rem 上限。尺寸规则必须同时匹配英语原路径与八语内容寻址路径；更新共享 CSS 后，需重建冻结发布产物，不能只修改历史快照。


SlimPower H1（JE-1000E-WH / JP / ja）使用[批准的日文冻结源](../../manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-no-cover-reviewed/README.md)，保留原候选与原稿文字、图框和安全符号。按操作者“封面 不要放进去网页版里面啊”，新 Web 版本从安全说明开始，印刷封面仅保留在原稿与来源存档；其余 16 章逐字节保持。`approval.json` 绑定原稿哈希、已审候选及独立章节/组件要求；回放前先验证批准身份，再通过共享 Manual IR / ComponentSpec 输出。日规沿用现有区域准入，不登记 phase2 或提升全局资产。正式发布仍按 Git-only 单语凭据、Hello-Docs 生成式发布 PR、RTD 回执/资源和桌面手机逐段核验，打印版本未知时保持未知。

JBP-1000B-WH / JP / ja 的 [Web 版式版本](../../manual_sources/JBP-1000B-WH/JP/ja/git-20261009-3aa6c003-web-layout/README.md) 由包内 `derive_web_layout.py` 从已批准原生包机械派生，原生包与其发布凭据保持不变。按操作者“全部修，一次做完”“封面和目录 不用体现在web版面上”并参照 JE-1000F 日文 Web：导航与印刷目录 12 章一致，二级内容不再升为章，原稿并排的安装步骤合为整行图（跨面板插图完整），标签字号按原稿 pt 与面板宽度生成；日文措辞与 `*_text` 字段不变，由单元测试比对可见文字。操作者于 2026-10-09 审阅对比图后指示“上线提交发布”，`approval.json` 绑定全部 `source/` 输入哈希；工程 PR 由操作者审核合入，合入后在实际 main 提交上封存 Git-only 发布证据并提交 Hello-Docs 发布 PR。

JA-AD500A-SIL / JP / ja（Jackery DC Input Module）的 [Web 版式候选](../../manual_sources/JA-AD500A-SIL/JP/ja/git-20261009-ac3a1f82-web-layout/README.md) 由包内 `derive_web_layout.py` 从已批准包 `git-20261008-ac3a1f82-reviewed`（MA-272）机械派生，已批准包与其发布凭据保持不变。沿用 JBP-1000B-WH JP 的规则：印刷封面标识行不进入 Web，页面从「お買い上げありがとうございます。」开始，导航即印刷的五个章节条；粗体、原稿换行、灰色面板与胶囊由页面局部 `source/presentation.css`（IR `source_stylesheet`）和 RST 标记实现，共享组件与共享 CSS 不改；同梱品说明书插图由共享资产管线重裁补全右边框，其余插图逐字节不变。日文措辞不变，由单元测试证明可见文字（含顺序）= 批准文字 − 封面行。操作者确认以仓库这份 PDF 为准、欢迎语保留、不加图标，审阅逐页对照后于 2026-10-09 指示“上线提交发布”；`approval.json` 绑定全部 `source/` 与 `assets/` 输入哈希。工程 PR 由操作者审核合入，合入后在实际 main 提交上封存 Git-only 发布证据并提交 Hello-Docs 发布 PR。
