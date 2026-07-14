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
| **子节胶囊 subbar**(OPERATING INSTRUCTIONS / USER MAINTENANCE INSTRUCTIONS) | 313×13.9pt,**全圆(stadium,r=h/2)** | subbar 盒(components_safety.tex) | `comp_subbar_arc`(2.45mm=半高)、`comp_subbar_pad_*` | `capsule_xml(bottom_only=False)`(stadium:r=半高) + `heading_text(level=2)`，文字框 `VerticalJustification=CenterAlign` | ✅ 已统一:`\safetysubbar`=BrandDark 全圆 tcolorbox + `\HBTypeSubbar` 白字；文字光学中心残差≤0.33pt |
| **H2 行内标题**(● POWER ON/OFF 等) | 无底色,`●` + Heavy 大写 | `\HBTitleLevelTwo` + `●` 前缀 | `type_title_l2_font_*` | `stories.add_prose_story` h2 分支(`● ` 前缀,HB Title L2 / Gilroy Heavy) | ✅ 字重、字号和纵向节奏一致 |
| **spec 小节头**(● GENERAL INFO) | 无底色 `●`+粗体 | `\specsectiontitle` | `spec_titles.csv` 本地化 | `add_spec_story`(HB Spec Section + `●`) | ✅ 一致 |
| **TOC 大标题**(TABLE OF CONTENTS) | **纯深色大字,无底条** | 目录页模板 | — | `page_toc` 标题(无填充框 + 深色大字) | 曾误做成深色圆角条,已改回 |
| **TOC 语言条**(EN English … 01-18) | 311.81×15.852pt,**圆角矩形 r=4.753pt**(左侧保留 6.346pt 直边),白字,右侧页码区间 | — | — | `page_toc` 专用量测几何 + `capsule_xml(corner_radius=4.753)` | 不属于 subbar 全圆族；生产 PDF 矢量坐标逐点校准 ✅ |

## 盒/面板族

| 样式 | 模板实测 | LaTeX | layout_params 键 | IDML 组件 | 备注 |
|---|---|---|---|---|---|
| notice 条(NOTE/TIP/CAUTION/WARNING) | 整宽灰面板；左侧 49.04pt 左圆右方白色标签栏；正文 6.5pt；项目符号 4.8pt | `\HBCalloutBlock` + `\HBCalloutBullet` | `comp_tip_arc` / `comp_caution_label_width` / `comp_callout_*` / `type_tip_*`；IDML 光学校正使用 `idml_callout_*_baseline_shift` | `components/notice` 四层锚定组（灰底、白标签板、标签文本框、正文文本框），原生 `HB Callout Label` / `HB Callout Body` 段落样式；page03 TIP 复用同一量测 | ✅ LaTeX→InDesign 最大残差 0.029pt；标签逐字透传 RST/线上表进入 IR 的源值，渲染器不得改词、复数化或提供默认文案；缺标签时构建失败 |
| note box | 灰圆角、按正文真实行数自适应 | `\HBNoteBlock` | 同上 | 同上；Gilroy 字宽估算后固定可编辑组高，避免 auto-size 覆盖下一段 | ✅ |
| 操作面板 oppanel | 圆角浅灰描边外框,无内网格 | 操作面板盒 | — | `components/oppanel`(锚定描边框 HB Border K10 1.1pt r10 auto-height) | ✅ #642 |
| spec/LCD/正文数据表外框 | 深色圆角描边 + 灰色表头/label 列 + 内部网格；单元格文字纵向居中；文字离左边界一个字符位 | `HBSharedDataTable`；spec、LCD、Auto Resume、Key Combinations、Troubleshooting 只声明列与行语义，列为 `m` / 内容盒为 `[c]` | `comp_table_outer_arc` / `comp_table_outer_rule` / `comp_data_table_*` / `comp_table_text_indent` | `components/rounded_table` 公共容器：“圆角背景 + 方形可编辑内容框 + 四角弧外遮罩 + 顶层描边”；正文正式表占满正文栏宽，字符缩进只落在 cell；`indesign_finalize.jsx` 按原生行高收紧每段 LCD 壳体 | ✅ 灰色单元格填充不会穿出圆角；表格仍保持原生可编辑；LCD 按同一分段规则生成多个完整圆角表，LaTeX/InDesign 共用 `lcd_table_layout.py`；英/法/西及短尾段均不会留下底部白带；源编号逐值透传，不得按行序重编 |
| Meaning of Symbols 表 | 圆角描边 + 首列 K05 浅灰 + 内部网格；左右表按各自内容高度收口 | `HBSymbolTable` / `HBSymbolTwoColumnTablesSplit` | `comp_symbol_*` | `pages._symbols_signal_table` / `_symbols_icon_table`；`indesign_finalize.jsx` 累加原生 `row.height`，同步收紧内容框和圆角外框 | ✅ 英/法/西首列统一浅灰；`fitted_symbol_table_shells` 记录最终化数量；短列不再保留底部白带 |
| inbox 三卡 | 圆角卡片 + 13.785pt 圆形编号，10.912pt Medium 白字 | inbox card tcolorbox | `comp_inbox_card_arc` | `components/inbox` + page03 卡片框；编号框和字均纵向居中 | ✅ 编号字形中心与圆心残差 0.003pt |
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
| 列表 | `type_list_font_size/leading`(5.4/6.4) | 5.4pt Regular 两线一致 | notice 内的列表另由提示框组件做 3.4pt 悬挂缩进 |
| 故障表表头/错误码 | `type_data_table_header_font_size`(6.6) / `type_trouble_code_font_size`(8.0) | 6.6pt Heavy / 8.0pt Bold；正文表表头与 LaTeX `HBFontHeavy` 一致 | 内线 0.25pt、外框 0.57pt，均使用品牌深灰 |
| 规格分组/左列标签 | `type_spec_section_font_size`(8.0) / `type_spec_label_font_size`(6.0) | 8.0pt Bold / 6.0pt Medium，与生产原稿一致 | 内线 0.50pt、外框 0.75pt，均使用品牌深灰 |

坑:type_system.tex 曾有两个 `\HBTypeSubbar`(providecommand 先到先得),#645 误加的重复宏(title_l2 8.6 Heavy)压住了原生宏(subbar 键 6.6 SemiBold)——已删,参数表原值恢复生效。

## 机制备忘(锚定框铁律)

- 锚定子故事必须在 designmap 中声明于宿主故事**之后**(前向引用),否则孤儿空框;`st_anchor_` 前缀 + `package.designmap_xml` 排序负责此契约(嵌套一层=块内倒创建序)。
- 内联锚定用子元素 `<AnchoredObjectSetting AnchoredPosition="InlinePosition">`;写成 TextFrame 属性会被静默丢弃。
- 圆角一律用贝塞尔路径本体(`rounded_path_geometry` / `bottom_rounded_path_geometry`);Corner 属性在生成的锚定框上不可靠。
- 标题胶囊、卡片编号及 safety-tail 的 WARNING/DANGER 单元格均显式使用 `CenterAlign`；全大写标签另做字形光学基线修正，不能只依赖段落默认顶对齐。
- LCD 图标单元格显式使用 `CenterAlign`，仅保留实测 0.6pt 光学校正；禁止恢复旧的 8.9pt `BaselineShift` 硬推定位。最终 9 个英文图标中心残差均为 0.00pt。
- `PRODUCT OVERVIEW` 下的产品部位标注网格属于待替换的 AI 插画内容，不进入正式数据表组件，也不参与表格样式验收。缺少最终 AI 图时，LaTeX 与 InDesign 的页码/分页只记录、不作为样式验收门槛。
- notice 列表正文使用 3.4pt 悬挂缩进；项目符号与正文拆成独立字号运行。提示框按 Gilroy 实际字宽预估换行并固定组高，避免 auto-height 向下覆盖；跨页 CAUTION 到下一标题的间距为 2.69pt（LaTeX 2.68pt）。
- `AutoSizingType="HeightOnly"` 导入生效;参考点必须 `TopCenterPoint`(Bottom→Object-is-invalid);路径高度过估(框只向下贴合)。表格外框不使用通用 auto-size；LCD 在最终 InDesign 合成后由 `fitLcdTableShells` 累加原生 `row.height`，同步收紧背景、内容框、底部遮罩和描边，预检以 `fitted_lcd_table_groups` 记录处理数量。Meaning of Symbols 的信号词/图标表由 `fitComposedSymbolTableShells` 独立量测和收口，预检以 `fitted_symbol_table_shells` 记录处理数量。
