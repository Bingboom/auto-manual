# IDML 样式映射清单:模板 → LaTeX → 组件化 → InDesign

单一参数源是 [`data/layout_params.csv`](../../data/layout_params.csv):它生成 LaTeX 的
`params.tex`(`HBcomp_*` / `HBtype_*` 宏),同时被 IDML writer 以 `writer.params` 读取。
两条渲染线的样式改动都应该落在这张表或本清单指向的组件上,不逐页改。

模板基准:`Jackery Explorer 1000 User Manual V2.0`(58 页 InDesign 原稿);
"LaTeX 实测"取自已接受的发布产物 `manual_je1000f_us_publish_1.5.pdf` 矢量。

## 标题族

| 样式 | 模板实测 | LaTeX 宏(components_base.tex) | layout_params 键 | IDML 组件 | 备注 |
|---|---|---|---|---|---|
| **H1 章节条**(IMPORTANT SAFETY INFORMATION / MEANING OF SYMBOLS / WHAT'S IN THE BOX / PRODUCT OVERVIEW / LCD DISPLAY / OPERATIONS / UPS / CHARGING / TROUBLESHOOTING / SPECIFICATIONS / WARRANTY / APP SETUP) | 312×20.1pt,BrandDark,**上方直角、下方圆角 r≈5.8** | `\HBTitleLevelOne`:tcolorbox `sharp corners=north, rounded corners=south` | `comp_h1_pill_arc`(0.8mm)、`comp_h1_pill_pad_lr/tb`、`comp_h1_pill_width`、`type_h1_font_size/leading` | composed 页:`page_objects.capsule_xml(bottom_only=True, r=7.0)` + `heading_text(level=1)`(=HB Capsule Text @12.4pt);流式页:`page_objects.h1_pill_paragraph`(锚定框,同几何) | ⚠ 圆角三个数并存:LaTeX 0.8mm≈2.3pt、模板 5.8pt、IDML 7.0pt。IDML 取 7.0 与 composed 页一致(近模板);要全线统一改 `comp_h1_pill_arc` 后同步这里 |
| **子节胶囊 subbar**(OPERATING INSTRUCTIONS / USER MAINTENANCE INSTRUCTIONS) | 313×13.9pt,**全圆(stadium,r=h/2)** | subbar 盒(components_safety.tex) | `comp_subbar_arc`(0.8mm)、`comp_subbar_pad_*` | `capsule_xml(bottom_only=False, r=7.0)` + `heading_text(level=2)` | LaTeX 目前把它渲染成 H1 同形(312×14.8 上直下圆),与模板(全圆)不一致——LaTeX 侧待修 |
| **H2 行内标题**(● POWER ON/OFF 等) | 无底色,`●` + 加粗大写 | `\HBTitleLevelTwo` + `●` 前缀 | `type_title_l2_font_*` | `stories.add_prose_story` h2 分支(`● ` 前缀,HB Title L2) | ✅ 一致 |
| **spec 小节头**(● GENERAL INFO) | 无底色 `●`+粗体 | `\specsectiontitle` | `spec_titles.csv` 本地化 | `add_spec_story`(HB Spec Section + `●`) | ✅ 一致 |
| **TOC 大标题**(TABLE OF CONTENTS) | **纯深色大字,无底条** | 目录页模板 | — | `page_toc` 标题(无填充框 + 深色大字) | 曾误做成深色圆角条,已改回 |
| **TOC 语言条**(EN English … 01-18) | 312×15.9pt 全圆,白字,右侧页码区间 | — | — | `page_toc` 语言条框(fill BrandDark + rounded) | 全圆族 ✅ |

## 盒/面板族

| 样式 | 模板实测 | LaTeX | layout_params 键 | IDML 组件 | 备注 |
|---|---|---|---|---|---|
| notice 条(NOTE/TIP/CAUTION) | 整宽灰面板 311.8×23.2 圆角 + 白 chip 50.5×18.2 圆角 | notice tcolorbox | `comp_notice_arc` | `components/callout._rounded_notice`(锚定灰面板 r7 auto-height + 嵌套白 chip r5.5) | ✅ #640 |
| note box | 灰圆角 | notebox | `comp_note_arc`(2.4mm≈6.8pt) | 同上(notice 路径) | ✅ |
| 操作面板 oppanel | 圆角浅灰描边外框,无内网格 | 操作面板盒 | — | `components/oppanel`(锚定描边框 HB Border K10 1.1pt r10 auto-height) | ✅ #642 |
| spec/LCD/trouble 表外框 | 深色圆角描边(spec r≈5 sw0.75-0.87;trouble sw0.57)+ 仅横线 + label 列灰底 | `tableframe` 等 | `comp_table_outer_arc`(0.9mm) | 表格本体(竖线抑制+灰底)✅;**圆角外框未实现** | 锚定 auto-size 对表格按声明行高贴合(10.3/行)不可用;待走 composed 矩形路线(`rounded_outer_xml`/`ROUNDED_TABLE_OBJECT_STYLE`) |
| inbox 三卡 | 圆角卡片 | inbox card tcolorbox | `comp_inbox_card_arc` | `components/inbox` + page03 卡片框 | ✅(#636 校准) |
| warranty 大字卡 | 圆角框 + 26pt 大字 | warranty 盒 | — | `components/warranty`(HB Big Numeral 26pt) | ✅ #635 |
| 语言徽章 langtag(前言 EN/FR/ES) | 深色小 pill + 粗标题 | 前言宏 | — | `components/langbadge` | ✅ #634 |

## 机制备忘(锚定框铁律)

- 锚定子故事必须在 designmap 中声明于宿主故事**之后**(前向引用),否则孤儿空框;`st_anchor_` 前缀 + `package.designmap_xml` 排序负责此契约(嵌套一层=块内倒创建序)。
- 内联锚定用子元素 `<AnchoredObjectSetting AnchoredPosition="InlinePosition">`;写成 TextFrame 属性会被静默丢弃。
- 圆角一律用贝塞尔路径本体(`rounded_path_geometry` / `bottom_rounded_path_geometry`);Corner 属性在生成的锚定框上不可靠。
- `AutoSizingType="HeightOnly"` 导入生效;参考点必须 `TopCenterPoint`(Bottom→Object-is-invalid);路径高度过估(框只向下贴合);**对表格按声明行高贴合而非渲染行高**——表格外框不可走 auto-size。
