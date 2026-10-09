# 原始 PDF 与 Web 候选的差异记录

本记录以指定 PDF 的可见日文为准。原 PDF 未修改，型号为 JBP-1000B-WH（JP/ja），不是 JBP-2000B。文件 SHA-256 与 20 页物理页映射见 source_manifest.json。

## 结构与呈现差异

纸版目录换成 Web 章节导航，空白末页不输出。原文的换行合并，保修条款和 FF 高低温处理步骤恢复独立段落。文字、表格、注意事项及图外标注保持原生日文、可编辑和可搜索；没有把整页或参数表截图当正文。17 个章节的 source/document.json physical_pages 提供原页映射。

全局使用现有共享组件：ReferenceFigure、SymbolSignal、SymbolIcon、Inbox、LCDIcon、Operation、LCDMode、CalloutStrip、Troubleshooting、Spec、WarrantyLead、WarrantySection。未引入新公共配置、模板家族、共享渲染器或接口。source/presentation.css 控制封面和几幅窄竖图的源局部尺寸，并取消本份文档两张手机表格的共享最小宽度。LCD 数字编号在手机上仍覆盖原始引线位置。手机端的其他标注由共享 ReferenceFigure 机制排列在图下；几何标签次序沿用原页。

## 保留的原文疑点（待操作员审阅）

| 物理页 / 印刷页 | 可见原文 | Web 处理 |
| --- | --- | --- |
| 6 / 04 | オフ = 1回押す；オン = 3秒 | 按原文保留，未按其他型号习惯交换 |
| 6 / 04 | 充电指示灯说明引用 Jackery SlimPower H1 | 保留，不改成 Battery Pack |
| 17 / 15 | 充電温度 -20°C～45°C | 保留，与動作温度相同，待技术确认 |
| 17 / 15 | 入力/出カポート（カ） | 保留原文用字 |
| 4 / 02、17 / 15 | 图标固定标记 Li-ion 32；参数 LiFePO₄ | 两者都保留；无匹配共享标记时使用该页原始透明矢量 |
| 19 / 17 | 有償修理条款与“有償修理後の保証期間”连接 | 只恢复段落边界，未改词句 |

物理 13 / 印刷 11 的本机文字提取出现 `8..`，可见 PDF 只有 `8.`，因此 Web 使用可见的 `8.`；原始提取保留在 pdf_blocks.json。物理 15 / 印刷 13 的底层包含隐藏英文 `WARNING Ensure all products…`，但渲染结果显示日文；隐藏英文存档于 pdf_blocks.json，不重复放进日文正文。

## 插图复用与采集记录

先查 exact target（无已有目标包），再查相同型号/地区其他语言（无合适文件），最后查共享 Battery Pack / JP / LCD 图标。JBP-2000B/2000 Plus 的宿主和安装结构与本源不同，不能充当本机图。输入/输出功率、百分比、剩余时间及通用安全符号复用现有共享文件，字节与原路径 SHA-256 一致，详见 reuse.json。共享安全符号形状可能与源页略异，语义一致；共享 manifest 本身为 local-candidate，未声称已登记批准。

| 图类 | 候选与决定 | 背景 / 边界 |
| --- | --- | --- |
| 通用安全与 LCD 图标 | reuse.json 中指定共享文件；复制字节不变 | 独立透明图标，不保留表格底板 |
| Li-ion32、单电池连接标记 | 共享 Li-ion/多电池标记不匹配；native_icon_recipe.json 指定原页矢量 | 原始路径与固定标记、透明边缘保留 |
| 充电/环形电量/DC/错误标记 | SlimPower 原图与通用宿主标记不同，原页矢量选择 | 排除整格灰色底板，真实透明 |
| 封面、同梱品、安装、连接及充电图 | 各 panels 无合适同型号共享图，使用本 PDF 的 asset_recipe.json | 完整灰色面板、结构边框、放大气泡、产品白色表面和引线保留 |
| 车载充电独立文字胶囊 | 删除源页 drawing 5283；其余原始路径及裁切组保留 | 文本框由共享 CSS 重绘，caption-frame admission 通过 |

安装图裁切逐一对照源页；stand-preparation、wood-1-2、wood-4/6、concrete-1-2/3/4/5/6/7/8/9、power 和 car-charge 的四边边框已补齐。wood-installed 单独保存完整立柱与“壁の中にある細い柱(間柱)”标注。完整面板中的灰色产品/背景不按颜色删除。bare-art 检查和浏览器检查覆盖边界、原始裁切组、标注布局及移动端文字堆叠；透明图标与完整面板分别按语义判断。

所有 recipe 资产维持 quarantine / build_eligible=false，仅用于此次离线候选。未触碰资产登记、不可变 promotion contract、Base 或附件。源文件的文件名版本、metadata title、页数和哈希均独立记录，不由共享模板推断。

## 发布准入补充（2026-10-08）

操作者授权「上线提交发布」后，现有符号准入逐项将图标与原 PDF 的矢量、同一行文字及像素绑定。六个旧共享小图的语义虽匹配，但字形或灰度不同，无法通过严格比较，因此改用指定原 PDF 第 4 页的原生矢量共用变体。原 Li-ion32 图保持字节不变。七个新变体只登记于 Git 共用图标清单，维持 local-candidate，不提升线上资产登记。原复用尝试与哈希保留在 reuse.json 的 superseded_candidate；行范围、原文、绘图索引和比较记录见 symbol_release_admission.json。说明文字、其余底图、技术参数及原稿疑点保持。
