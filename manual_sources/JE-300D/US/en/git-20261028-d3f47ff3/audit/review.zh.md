# JE-300D US/en 审核要点（候选稿，未获发布授权）

来源：发布文档管理 Base 行 `reczz28SlRGJh85k`（物料号 38-0001-000960，项目号 HTE150）的英文单语 PDF，18 页，90×130 mm，全部转曲。
网页正文为逐行人工转录，已对照 300 dpi 渲染核对；英文原文未改动。共用参考版：JE-300D EU 英文 Web（phase2 模板构建）。

请操作员确认（默认按下列处理）：

1. 封面（p1）、目录（p3）不上网页；p2 IMPORTANT 作为首章；封底（p18）作为末章，章名取封面「CONTACT US」，按印刷顺序保留 Hong Kong Hello Tech Energy Co., Limited 与 JACKERY INC. 两段地址、电话、邮箱、网址和二维码，去掉电话/邮件/网址小图标。
2. 操作与充电面板按印刷面板整图裁取（只去掉面板外框），图内文字（On/Off/Press once、LED 三步说明、SolarSaga 40 Air x1、Vehicle 等）保留在图中，网页 alt 读出；面板内的灰色文字条（Prerequisite、能耗说明、LED 模式说明、USB-C 充电步骤、「* The car charging cable is sold separately.」等）改为网页正文段落；NOTE/CAUTION 框用共用 callout。
3. p7 购物车图标提示「The handle attachments can also be used for adjustable straps (sold separately).」改为加粗段落，不保留购物车小图标。
4. WHAT'S IN THE BOX 两张卡片用共用 inbox（编号由共用组件绘制），印刷 TIP 条作为 inbox 的 TIP。
5. 规格页 Multi-Port Output Combinations 的 1～5 口组合表用共用 HB-TABLE-REFERENCE（两列，带印刷表头），无普通表例外。
6. 符号表 7 个符号全部字节复用共用图库，无新增共用符号；LCD 图标 11 个中 3 个复用 JE-300E US 同图，其余 8 个用本稿原生矢量；FCC 标志复用共用 fcc_mark.svg。
7. 保修「Customer Support」三个邮箱印刷在同一行，网页分三行显示（文字未改）。

原稿保留原样、待原稿负责人确认的地方见 `source_manifest.json:source_concerns`（共 11 条），主要有：
- p4「temperature ranges :」冒号前空格；温度子项以「;」结尾；「Solar charge times depend …, place …」逗号连接。
- p14 STORAGE 只给摄氏温度；F7「open-circuited voltage」与「solar panel.The product」缺空格。
- p15 「1 ×」与「1×」空格不一致；DC 12V Port 额定 12V⎓10A Max，但组合表写 120W。
- p17 「hello.my@jackery.com (Philippines)」邮箱域名与国家不一致。
- 印刷对齐造成的双空格（p4、p5 FCC）按排版处理为单空格，不属改字。
