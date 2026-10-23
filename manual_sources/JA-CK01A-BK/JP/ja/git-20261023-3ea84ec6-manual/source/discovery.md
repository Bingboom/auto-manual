# 资产盘点与选材记录（Web 插图复用顺序）

源稿：操作员指定的飞书 wiki 文件（只读下载），
文件名「38-0001-000777 HTO862A-JP-JAK 说明书 RoHS REACH.pdf」，SHA-256 `3ea84ec6…d113`，只读下载。
PDF 为 Illustrator 单画板（2301×1613 pt），含 4 个 130×185 mm 面板（封面、p2 安全/规格/步骤1、p3 步骤2–4、p4 步骤5/QR）
及印刷图框；全部文字已转曲，无文本层、无位图。

提取前检索范围：`manual_sources/`、`data/manual_sources/`、`docs/renderers/web/assets/`（含 `shared/symbols`、`shared/buttons`）、
`docs/templates/word_template/common_assets/`、`docs/renderers/latex/assets/`；关键词 inlet / インレット / L14-30 / JA-CK01A /
HTO862A / Power Output Cable Kit。仓库内没有本产品（插座箱 + L14-30 电缆套件）的任何既有素材；
同名命中的 JE-1500D/JE-3000C/JHP-3600C 是电源本体的 AC 输入口，形状与内容不同。

| 图/槽位 | 查过的清单与候选路径 | 身份/内容核对 | 决定 | 新提取的具体理由 | 最终来源与哈希 | 背景/边界策略 |
| --- | --- | --- | --- | --- | --- | --- |
| 步骤1 拆前盖 | 上述全部清单；无匹配 | 本产品专有插座箱 | 新提取 | 查无可用素材 | 原稿 p2 步骤框 drawing 1584 内裁切，见 `asset_recipe.json` | 去掉装饰性步骤框（白底四角 whiteout），插图完整 |
| 步骤2 标记孔位 | 同上 | 同上；95mm/57.3mm 为图内尺寸标注 | 新提取 | 同上 | p3 drawing 1585 内裁切 | 同上；尺寸标注保留在图内 |
| 步骤3 钻孔/壁锚 | 同上 | 同上 | 新提取 | 同上 | p3 drawing 1588 内裁切，止于注意灰框上沿 | 灰框文字改为原生 `hb-text-panel` |
| 步骤4 固定 | 同上 | 同上 | 新提取 | 同上 | p3 drawing 1587 内裁切 | 同上 |
| 步骤5 接线 | 同上 | 同上；英文线色与 Groud Screw Terminal 为外部标签 | 复用底图改文字（本包内） | 同上；标签须为原生文字 | p4 drawing 1586 内裁切，标签字形与气泡 whiteout | 10 条原生标签按原稿坐标放置；气泡以共享 live pill 重建 |
| 警告三角 | `shared/symbols/manifest.json` warning/* | 原稿为实心深灰三角 | 未使用 | — | — | prepared-document 共用 Callout 只承载信号词（先例 JA-AD500A-SIL JP「不加图标」）|
| 封底 QR | 共用库无本产品 QR | 日本原稿 QR | 新提取 | 目标码与其他产品不同 | p4 [732, 871, 772, 911] pt，含圆角边框与静区 | 完整保留 |

不为此新建型号配置、资产注册表或构建管线；资产为 Git-only 候选（gate `quarantine`），不推广到注册表。
矢量重放（`retain_vector_drawings`）已试并放弃：该原稿依赖剪切路径与虚线，重放会露出隐藏几何（见 README）。
