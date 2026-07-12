# IDML 样式映射清单:模板 → LaTeX → 组件化 → InDesign

单一参数源是 [`data/layout_params.csv`](../../data/layout_params.csv):它生成 LaTeX 的
`params.tex`(`HBcomp_*` / `HBtype_*` 宏),同时被 IDML writer 以 `writer.params` 读取。
两条渲染线的样式改动都应该落在这张表或本清单指向的组件上,不逐页改。

模板基准:`Jackery Explorer 1000 User Manual V2.0`(58 页 InDesign 原稿);
"LaTeX 实测"取自已接受的发布产物 `manual_je1000f_us_publish_1.5.pdf` 矢量。

## 标题族

| 样式 | 模板实测 | LaTeX 宏(components_base.tex) | layout_params 键 | IDML 组件 | 备注 |
|---|---|---|---|---|---|
| **H1 章节条**(IMPORTANT SAFETY INFORMATION / MEANING OF SYMBOLS / WHAT'S IN THE BOX / PRODUCT OVERVIEW / LCD DISPLAY / OPERATIONS / UPS / CHARGING / TROUBLESHOOTING / SPECIFICATIONS / WARRANTY / APP SETUP) | 312×20.1pt,BrandDark,**上方直角、下方圆角 r≈5.8** | `\HBTitleLevelOne`:tcolorbox `sharp corners=north, rounded corners=south` | `comp_h1_pill_arc`(0.8mm)、`comp_h1_pill_pad_lr/tb`、`comp_h1_pill_width`、`type_h1_font_size/leading` | composed 页:`page_objects.capsule_xml(bottom_only=True)` + `heading_text(level=1)`(=HB Capsule Text @12.4pt);流式页:`page_objects.h1_pill_paragraph`(锚定框,同几何);半径统一走 `page_objects.h1_arc_pt`(读同一 CSV 键) | ✅ 已统一:`comp_h1_pill_arc`=2.0mm≈5.67pt(模板实测 5.8),LaTeX 与 IDML 同键单源 |
| **子节胶囊 subbar**(OPERATING INSTRUCTIONS / USER MAINTENANCE INSTRUCTIONS) | 313×13.9pt,**全圆(stadium,r=h/2)** | subbar 盒(components_safety.tex) | `comp_subbar_arc`(2.45mm=半高)、`comp_subbar_pad_*` | `capsule_xml(bottom_only=False)`(stadium:r=半高) + `heading_text(level=2)` | ✅ 已统一:`\safetysubbar`=BrandDark 全圆 tcolorbox + `\HBTypeSubbar` 白字;USER MAINTENANCE 页模板/US _review 页由 section 改 `\safetysubbar` 双载体 |
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
| spec/LCD/正文数据表外框 | 深色圆角描边 + 灰色表头/label 列 + 内部网格；单元格文字纵向居中 | `HBSharedDataTable`；spec、LCD、Auto Resume、Key Combinations、Troubleshooting 只声明列与行语义，列为 `m` / 内容盒为 `[c]` | `comp_table_outer_arc` / `comp_table_outer_rule` / `comp_data_table_*` | 表格本体(内部网格+灰底)✅；圆角外框仍待 composed 矩形路线 | LaTeX 已统一外框对象、内部网格与纵向居中；IDML 保持当前限制说明 |
| inbox 三卡 | 圆角卡片 | inbox card tcolorbox | `comp_inbox_card_arc` | `components/inbox` + page03 卡片框 | ✅(#636 校准) |
| warranty 专页/大字卡 | 灰底导语 + 悬浮标签圆角框 + 3/2 年双栏圆章 | `hb_latex_warranty.py` doctree 映射 + `components_warranty.tex` | `comp_warranty_*` / `type_warranty_*` | `components/warranty`(HB Big Numeral 26pt) | ✅ LaTeX 独占页与 IDML 组件化 |
| 语言徽章 langtag(前言 EN/FR/ES) | 深色小 pill + 粗标题 | 前言宏 | — | `components/langbadge` | ✅ #634 |

## 字号/字重收敛(2026-07-11 参数收敛轮,fitz 双线实测)

| 元素 | 共用键 | 双线实测 | 备注 |
|---|---|---|---|
| H1 盒字 | `type_h1_font_size/leading`(9.0/10.8) | 9.0pt 两线一致 | 字重 LaTeX=Heavy、IDML=Bold(IDML 未注册 Gilroy-Heavy,近似) |
| H1 条高 | `type_h1_font_leading + 2×comp_h1_pill_pad_tb + 1.45`(tcolorbox 盒模型修正) | 14.8pt 两线一致 | IDML 走 `page_objects.h1_bar_h_pt` |
| subbar 盒字 | `type_subbar_font_size/leading`(6.6/7.2) | 6.6pt Medium 两线一致 | \HBTypeSubbar 实渲染 Gilroy-Medium(SemiBold 字体缺→回退) |
| subbar 条高 | 常量 13.9(模板/发布 PDF 双实测) | 13.9pt 两线一致 | `pages.SUBBAR_H` |
| 正文/lead-in | `type_body_font_size/leading`(6.2/7.5) | 6.2pt Medium 两线一致 | \HBTypeBody=HBFontMedium;IDML HB Body 字重已改 Medium;安全页 lead-in 曾误映射 HB Title L2(8.6 Bold)已修 |
| 列表 | `type_list_font_size/leading`(5.4/6.4) | 5.4pt Regular 两线一致 | |

坑:type_system.tex 曾有两个 `\HBTypeSubbar`(providecommand 先到先得),#645 误加的重复宏(title_l2 8.6 Heavy)压住了原生宏(subbar 键 6.6 SemiBold)——已删,参数表原值恢复生效。

## 机制备忘(锚定框铁律)

- 锚定子故事必须在 designmap 中声明于宿主故事**之后**(前向引用),否则孤儿空框;`st_anchor_` 前缀 + `package.designmap_xml` 排序负责此契约(嵌套一层=块内倒创建序)。
- 内联锚定用子元素 `<AnchoredObjectSetting AnchoredPosition="InlinePosition">`;写成 TextFrame 属性会被静默丢弃。
- 圆角一律用贝塞尔路径本体(`rounded_path_geometry` / `bottom_rounded_path_geometry`);Corner 属性在生成的锚定框上不可靠。
- `AutoSizingType="HeightOnly"` 导入生效;参考点必须 `TopCenterPoint`(Bottom→Object-is-invalid);路径高度过估(框只向下贴合);**对表格按声明行高贴合而非渲染行高**——表格外框不可走 auto-size。
