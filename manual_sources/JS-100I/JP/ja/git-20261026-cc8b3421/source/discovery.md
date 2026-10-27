# 资产盘点与选材记录（Web 插图复用顺序）

源稿：操作员指定的飞书 wiki 文件「Jackery SolarSaga 100 Air说明书.pdf」（节点 `TC9MwqDAsihTJ0kPlsJcVj4JnNf`，
只读下载），3,403,400 字节，SHA-256 `cc8b3421…513e6f`。12 页 130×185 mm 竖版，Illustrator 竖版导出
（creator「PDF portrait export」），全部文字已转曲，无文本层、无位图；每页引用同一个画板表单并裁切到本页。

提取前检索范围：`manual_sources/`、`data/manual_sources/`、`docs/renderers/web/assets/`（含 `shared/symbols`、
`shared/buttons`、`js100i_eu_en/`、`js100i_eu_shared/`、`js100i_eu_added/`）、`docs/templates/word_template/common_assets/`、
`docs/renderers/latex/assets/`；关键词 JS-100I / js100i / SolarSaga 100 Air / solar。命中的是同一产品的
JS-100I EU 网页版（`docs/renderers/web/js100i_eu_en_illustrations.json` 绑定的 13 张英文裁图与九语共用的 16 张无字底图）。
逐张把 JP 原稿图与 EU 底图并排比对（200 dpi），只按图形内容判断，语言和页码不是重提理由。

| 图/槽位 | 查过的清单与候选路径 | 身份/内容核对 | 决定 | 新提取的具体理由 | 最终来源与哈希 | 背景/边界策略 |
| --- | --- | --- | --- | --- | --- | --- |
| 同梱品① 本体 | `js100i_eu_en/inbox_panel.png` | 同一面板线稿 | 复用 | 不适用 | EU 原路径，`bfe453b3…` | 原样（白底小卡图） |
| 同梱品② 收納バッグ | `js100i_eu_en/inbox_bag.png` | 同一收纳包线稿 | 复用 | 不适用 | `7995365a…` | 原样 |
| 同梱品③ ケーブル | `js100i_eu_en/inbox_cable.png` | 同一线缆线稿 | 复用 | 不适用 | `0d1e2c82…` | 原样 |
| 同梱品④ 取扱説明書 | `js100i_eu_en/inbox_manual.png` | EU 为通用文档图标；JP 画的是本说明书封面缩略图 | 新提取 | 图形内容不同 | p3 [58.5, 188.0, 100.5, 246.5] pt | 只裁图形，卡片框与编号由共享 Inbox 绘制 |
| 本体前面 | `js100i_eu_en/product_views.png` | EU 图内烤入英文标签并把前后视图合成一张；无无字底图 | 新提取（复用底图不可行） | 无可用无字底图 | p3 [72, 418, 338, 468] pt，标签字形 whiteout | 白页底；引线保留，标签为原生文字 |
| 本体背面 | 同上 | 同上 | 新提取 | 同上 | p4 [26, 38, 346, 147] pt，标签与「本体背面」字形 whiteout | 同上，4 条原生标签 |
| 展開 1 | `js100i_eu_shared/unfold_1.png` | 收纳包＋面板、两条箭头一致 | 复用 | 不适用 | `401a4aed…` | EU 透明底（步骤框为装饰） |
| 展開 2 | `js100i_eu_shared/unfold_2.png` | 三个展开阶段一致 | 复用 | 不适用 | `95df1463…` | 同上 |
| 展開 3 | `js100i_eu_shared/unfold_3.png` | 背面两支架一致 | 复用 | 不适用 | `a697833e…` | 同上 |
| 展開 4 | `js100i_eu_shared/unfold_4.png` | JP 画的是另一款便携电源（侧视） | 新提取 | 电源型号/外观不同 | p5 步骤框 84144 内，避开圆角 | 白底，步骤框外框不入图 |
| 収納 1 | `js100i_eu_shared/fold_1.png` | 平铺面板一致 | 复用 | 不适用 | `a8d513b1…` | EU 透明底 |
| 収納 2 | `js100i_eu_shared/fold_2.png` | 两个折叠阶段一致 | 复用 | 不适用 | `816b24b4…` | 同上 |
| 収納 3 | `js100i_eu_shared/fold_3.png` | EU 图上箭头被裁掉一半、下箭头缺失；JP 两条箭头完整 | 新提取 | 内容不同（箭头） | p6 步骤框 83999 内，避开圆角 | 白底 |
| 8020 接続 | `js100i_eu_shared/dc8020.png` | JP 为另一款电源与端口特写 | 新提取 | 电源型号/接口特写不同 | p6 灰面板 38736 整块 | 灰底圆角面板完整保留；标签与白色气泡用同面板空白灰块覆盖（copy_pdf_region），文字为原生标签 |
| 7909 接続 | `js100i_eu_shared/dc7909.png` | JP 为 Explorer 1000 与直型转接头；EU 为另一款与 L 型转接头 | 新提取 | 同上 | p6 灰面板 39337 | 同上 |
| USB-C 接続 | `js100i_eu_shared/usbc.png` | JP 电源型号、面板布置不同 | 新提取 | 同上 | p7 灰面板 41068 | 同上 |
| SolarSaga アダプター | `js100i_eu_shared/parallel.png` | JP 电源型号、两组面板布置不同 | 新提取 | 同上 | p7 灰面板 90139 | 同上，3 条原生标签 |
| 太陽角度インジケーター | `js100i_eu_shared/angle.png` | 面板角度、射线与放大圆比例不同 | 新提取 | 图形不同 | p8 灰面板 7331 | 同上，3 条原生标签 |
| 判定（○/×） | `js100i_eu_shared/angle_choice_1.png`、`angle_choice_2.png` | 对勾/叉与指示器图形一致 | 复用 | 不适用 | `ea9307d4…`、`fcec9055…` | EU 透明底；JP 灰卡片底不复制，说明文字为原生正文 |
| デバイスへの電力供給 | `js100i_eu_shared/device.png` | JP 电源型号与适配器特写不同 | 新提取 | 图形不同 | p9 灰面板 31632 | 同上，6 条原生标签（含注释） |
| ゴムプラグ | `js100i_eu_shared/dust.png` | 适配器与橡胶塞特写一致 | 复用 | 不适用 | `1e26a0f6…` | EU 透明底；注释为原生 `hb-text-panel` |
| 封底 QR | 共用库无本产品 JP QR | 日本原稿 QR | 新提取 | 目标码 | p12 [303, 453, 340, 490] pt | 圆角框与静区完整保留 |
| 警告三角、联系方式图标 | `shared/symbols/manifest.json` warning/* | 装饰性图标 | 未使用 | — | — | prepared-document 共用 Callout 只承载信号词（先例 JA-AD500A-SIL JP「不加图标」） |

复用文件按字节复制到 `assets/`，`source/asset_decisions.json` 记录原路径与 SHA-256，`tests/test_js100i_jp_web.py`
校验与仓库原文件逐字节一致。新提取图由 `derive_assets.py` 经共用 asset pipeline 生成（gate `quarantine`，
不推广到注册表，不新建型号配置）。矢量重放未采用：该原稿含 `qu` 四边形路径（重放不支持）且依赖剪切路径。
