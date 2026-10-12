# Workflow guide: Web rendering on public IR

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

The prepared Web Inbox now passes its three cards and optional internal TIP
through public IR before figure protection. Source language and target context
are preserved; malformed card/tip rows or inconsistent IR fail before partial output is applied.
Rich text, links, image references and existing EN/FR/ES appearance are retained.
This does not admit new targets into the approved figure contract or change
Word/IDML output. Other composite figure callouts remain separate work.

For new whole-document Web builds, Inbox is no longer a temporary page-level
IR detour. Inbox, Overview, FCC, Specifications, Callout, governed Operation,
hybrid LCD Mode, Warranty, LCD Icons, Troubleshooting, both Symbols tables,
App and governed Reference Figure
instances are written once into ordered `manual-ir/v2` flow
and replayed from those embedded specs. Their source projectors run only while
assembling a new package; opening or publishing the frozen package does not
reparse RST/CSV or rediscover those eighteen component types from HTML. Historical
packages remain supported. German `JAHRE` and Italian `ANNI` use the same
component-owned 3/2 numeric badge adapter; compact Korean `3년` / `2년` headings
are parsed by that same language-neutral warranty component. Operation instances
are embedded only when the resolved target overlay grants figures; other product
skeletons keep their distinct operation panels as neutral editable flow until a
matching overlay grants them, rather than inheriting JE-1000F's
five-panel geometry. LCD and Symbols icon collections use
one repeatable, ordered asset role, so every row remains bound to the correct
packaged image. LCD, Troubleshooting and Symbols remain editable native tables,
not screenshots. App download, its inline control, and add-device panels retain
their localized copy and role-bound shared artwork in the same ComponentSpec.
Each Reference Figure retains its complete semantic fallback; an approved
composite additionally records target replace key, locale, packaged asset key,
content SHA-256 and source-fragment SHA-256. Exact-locale figures never fall
back to another language. The live semantic composition prevents broken output,
but for a finished-figure coverage slot it remains `editable-fallback` debt and
cannot pass unless that exact pre-existing row is in the ratcheted baseline.

Prepared Web FCC also passes through public IR. Its opening copy, measures,
column split and mark binding can be replayed without reopening the source page.
Invalid semantic data or an inconsistent mark binding stops the transform before
partial output. Existing EN/FR/ES copy, paragraph normalization, figure admission
and Word/IDML output are unchanged; this does not change legal text or approve
an additional region.

The signal-word legend also uses public IR while retaining its localized labels
and rich meaning cells. Malformed final labels, ambiguous tables or unsupported
row spans fail before the source table is partly changed. Existing EN/FR/ES
output and surrounding symbol-pair tables are preserved; no additional target
is admitted by this change.

The adjacent icon/meaning table now follows the same public IR boundary while
keeping its left-six/right-five panels. Invalid icon bindings, row spans or
nonempty unused cells stop before partial output. Images, rich meaning cells
and EN/FR/ES whole-page output are preserved; the existing signal legend and
target-admission rules are unchanged.

LCD semantics now come from the assembly planner's `lcd_icons` CSV page identity
or an explicit `hb-lcd-icon-table` declaration, rather than a filename or US
figure grant. Renamed slots and JP targets use the same four-column projection;
ordinary undeclared tables stay ordinary. RST and standalone `{lcd-icons}` MyST
share validation: exactly four unspanned cells, one icon, and nonempty number,
name and description. Malformed rows fail instead of being padded or truncated.
Status line breaks, inline emphasis, lists, icon sources and row order remain
authored content. The scrollable table can also receive keyboard focus; artwork
approval rules remain unchanged.

App download's store and QR columns also consume public IR. Both live copy
columns, links/emphasis, the original semantic image and artwork bindings survive
serialized replay. Invalid or ambiguous source content stops before changing the
page. The download, inline-control, and add-device variants now enter the frozen
whole-document IR as one registered App component family.

The App add-device inline button also consumes public IR. Its localized
accessible name and surrounding sentence, emphasis, links and images survive
replay; ambiguous or incomplete labels fail before changing the page. Existing
three-language output and Pandoc protection remain unchanged. Governed Charging
and App reference panels use the registered Reference Figure family described
above; missing composites remain visible semantic fallbacks but do not count as
finished artwork.

- The LCD screen-mode panel remains searchable HTML while matching the template's rounded illustration-plus-table composition across EN/FR/ES. The AC/DC Auto Resume matrix also remains searchable HTML with equal-width columns, a light left column, white right column, dark full-grid rules, and a true two-row Battery SOC cell. On phones each compact table scrolls inside its own frame instead of widening the page.
- The EN/FR/ES Troubleshooting table remains searchable HTML with the PDF's rounded dark frame, full grid, 14% light error-code column, and 86% white corrective-measures column. F6/F7 actions keep their source line breaks through Pandoc. The four Specifications tables use a matching protected 31%/69% label/value grid and preserve row-spanning labels; the web transform removes the authored bullet glyph so the shared heading theme shows one section dot rather than two, and raises both governed `①` references as semantic superscripts. Both table types scroll inside their own frame on phones.
- Warranty remains searchable shared HTML independently of the approved-figure target list. JE-1000F US keeps EN/FR/ES, while JE-1000F EU also inherits the same number-badge component for EN/FR/ES/DE/IT (`YEARS`, `ANS`, `AÑOS`, `JAHRE`, `ANNI`) without copying page CSS or target code. Both the current shared-template form (`warranty-lead` / `warranty-section` semantic containers) and an older flat review page are accepted; only those governed containers are unwrapped before HTML conversion so their nested headings are retained. The two opening paragraphs form the PDF-like rounded notice and local-law note; all six localized H2 headings stay theme-controlled and appear as floating dark labels on rounded cards. Five sections are ordinary copy cards, while Warranty Period is rebuilt from the source table as localized 3-year/2-year columns at approximately 61%/39% on desktop and one column on phones. The source 50/50 table geometry is removed, but email links, exclusions and every localized paragraph remain live content. `figure_targets` still controls target-specific Overview/Operation/Charging geometry and approved composite admission; this shared warranty inheritance does not grant artwork reuse.
- RTD also applies the shared IDML-derived responsive theme: brand-dark title bars, compact heading levels, rounded tables and warning/note groups, consistent spacing, and proportional images. A browser with licensed Gilroy installed uses it; other browsers use the declared system fallbacks. The site intentionally reflows on phones and does not claim the fixed page count or exact pagination of IDML/INDD.
- The web export protects each semantic callout before Pandoc and restores it afterward. WARNING, DANGER, CAUTION, and NOTE therefore keep one shared class structure, one light rounded visual treatment, and the theme's approximately 16% label / 84% body desktop split; every callout on a page shares one label-column width, sized to the page's widest label, so localized labels never break mid-word and the first-column boundary stays aligned. Pandoc does not add a 50/50 `colgroup` or an empty header row. On phones the same component stacks vertically.
- Web tables keep words whole and stay inside their frames. On desktop the Troubleshooting, LCD, Auto Resume, and key-combination tables fit the reading column without a scrollbar; only narrower screens scroll inside the table frame. Long localized warning badges (fr `AVERTISSEMENT`, uk `ПОПЕРЕДЖЕННЯ`) widen the MEANING OF SYMBOLS label column instead of overflowing, and the Troubleshooting code header wraps at spaces. On phones table columns grow to fit their longest word; the only exception is a raw HTML table (no scroll frame) on screens narrower than 520 px, which may still split a word so that it is not cut off at the page edge.
- Scientific subscripts and specification superscripts are protected across the same Pandoc step, so source notation such as ``V\ :sub:`oc``` renders as semantic `V<sub>oc</sub>` and governed `①` references render as `<sup>①</sup>` in every language rather than showing literal inline Markdown notation.

Web 规格表已接入公共 IR 校验，构建命令不变。Web 构建会保留规格中的链接、强调、
换行和脚注，不再借用 Word 的纯文本抽取重建。任何声明规格表不合法时，本次规格
转换整体失败，避免只转换前半页。新整本 Web 包已把规格 ComponentSpec 写入 v2
中立 flow，并从冻结 IR 直接重放；Word/LaTeX/IDML 的整本入口和 JP 原生排版仍需
分别验收。


LCD 图标表和故障排除表也已接入同一条公共 IR 消费路径，主构建与独立 Markdown
站点共用，命令不变。图标替代文字、列表、链接、图注和表头仍来自原文；同一批
表格中有一张不合法时，整批转换失败，不留下半页已转换的结果。这仍是表格级
组件接入；整本 v2 flow 已建立，其他组件和四端 adapters 尚未全部迁移。


独立 Markdown 的 `{spec-table}` 也已复用公共规格表 IR，不再单独计算合并行和
拼装表格。参数标题继续用作组件标签，不增加可见标题；上下标和空标签续行保留，
裸圆圈脚注编号使用统一上标样式。规格表、LCD、故障排除三类表格已在两种 Web
入口接通；它们写入整本 v2 IR 并由四端共享消费仍是后续组件刀。


生成 Web 的警告／提示框在 Pandoc 转换前后也已通过公共 IR 交接，构建命令不变。
框内原文、链接、列表和图片保持原样；IR 损坏或声明的标签／正文结构不完整时构建
失败。已整体保护的复合插图内提示框仍待迁移；整本 Web 的 v2 flow 底座已完成，
但复合组件和 JP 原生版式仍需独立验收。


独立 Markdown 的 `{callout}` 也已接入同一个公共 IR 消费器。正文仍由 Sphinx
处理，内部链接、图片、列表和强调保留；自定义标签的 `:variant:` 与配置语言会
一起进入校验。提示框内嵌表格或其他提示框暂不受共享契约支持，会带来源位置报错，
不会截断后继续输出。命令和编辑位置不变。
