# 原稿 PDF 与 Web 候选的差异记录

PDF：`source/original.pdf`（SHA-256 `3ea84ec6…d113`，1 个物理页，4 个印刷面板）。操作员 2026-10-23 指示
「开两个窗口 把这俩说明书 走git only转网页文档」，沿用 JBP-1000B-WH / JA-AD500A-SIL JP 规则：封面和目录不上网页，
参考 JE-1000F 日语网页说明书，不改动任何日文原文。本 PDF 无印刷目录。

所有日文措辞按 `source/transcription.json` 逐字转录（原稿文字已转曲）；`tests/test_ja_ck01a_bk_jp_web.py`
证明 Web 可见文字（含顺序，忽略空白）= 转录的 Web 行。

| 位置 | 原稿 | Web 候选 | 依据 |
| --- | --- | --- | --- |
| 封面 | Jackery 标志、型番、产品名、取扱説明書、国内専用/For use only in Japan、产品图 | 不进入 Web | 封面不上网页 |
| 封面 | 欢迎语 + 四条「•」说明 | 页面开头：粗体欢迎语 + 「・」列表 | JA-AD500A-SIL JP 先例 |
| 封面 | カスタマーサポート 胶囊 | 移到页尾共享灰色面板（与封底 QR 一起） | 封面去掉后联系方式不丢失 |
| p2 警告 | 白底描边框，实心三角 + 警告，正文编号 1–3 | 共用 HB-CALLOUT-STRIP/warning，无三角图标 | prepared Callout 只承载信号词；先例「不加图标」 |
| p2 主な仕様 | 标题栏右侧「Model: JA-CK01A-BK」 | 标题栏下第一行粗体 | prepared RST 章节标题不能携带共享 `hb-heading-model` |
| p2 主な仕様 | 4 行表 | 声明的普通表，沿用共享 `manual-spec-table` | HB-TABLE-SPEC 需要原稿印刷的小节标题 |
| p2–p4 步骤 | 「●」+ 编号文字，浅灰圆角步骤框 | 去掉装饰性 ● 与步骤框；编号原样保留（1./2. 无空格，3./4./5. 有空格） | 装饰元素 |
| p2–p4 注意 | 步骤框内灰色胶囊 | 插图后的共享 `hb-text-panel` | 正文必须为原生文字 |
| p4 接线图 | 图内文字（气泡说明、Green/White/Black/Red、Groud Screw Terminal） | 原生标签放在原坐标；气泡（含尾巴）改为共享 live pill（无尾巴） | Web 插图规则：外部标签为原生文字 |
| p4 QR | 圆角框 QR | 页尾 96 px | 原稿尺寸比例 |
| 图框外 | 修订表、图框、尺寸/材质说明、第二个 QR | 不进入 Web | 印刷生产信息 |
