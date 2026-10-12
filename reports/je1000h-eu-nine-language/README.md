# JE-1000H EU 三种新增语言本地验收

Status: active

只补充葡语、荷语、波兰语；保留既有英、法、西、德、意、乌克兰语。最终完整源包为
`candidate-23/{pt,nl,pl}`，HTML 为 `preview-23/{pt,nl,pl}`，每语 16 章。
没有新建渲染器或修改共用 CSS，没有发布、合并或写入飞书。

## 本地预览

预览服务器端口 18930，仅绑定 `127.0.0.1`：

- [葡语](http://127.0.0.1:18930/preview-23/pt/manual_je1000h_eu_pt.html)
- [荷语](http://127.0.0.1:18930/preview-23/nl/manual_je1000h_eu_nl.html)
- [波兰语](http://127.0.0.1:18930/preview-23/pl/manual_je1000h_eu_pl.html)

重启服务：`python3 -m http.server 18930 --bind 127.0.0.1 --directory reports/je1000h-eu-nine-language`。
这些地址是本机候选预览，不是 RTD 发布地址。

## 用户指出的版面问题

1. 节能图先修过重复时钟，现按最新要求保留完整原生面板及单个时钟/`3s`；见下节。
2. AC 灰色前置条件框遮挡 AC1 圆图；DC/USB 同类框也过长。缩短后手机端仍遮引线，
   因此三语前置条件均保留为图前独立原生文字，各出现一次，图内只保留开关操作标签。
3. 排查了主电源、AC1/AC2、DC/USB、LED、节能、App 标签、概览、LCD、充电及规格表。
   1280×720 与 390×844 下没有整页横向溢出、失败图片或图内提示框遮挡。
   长表格沿用共享容器内横向滚动。扩容电池图下缘相邻配件框线也已从裁切中排除。

[桌面操作截图](screenshots/pt-desktop-operations.png) ·
[手机操作截图](screenshots/pl-mobile-operations.png) ·
[节能图截图](screenshots/pt-desktop-energy.png) ·
[浏览器指标](evidence/browser-metrics.json)。其余逐语截图保存在 `screenshots/`。

## App 灰底与共用截图（candidate-23）

按键说明图恢复原稿完整灰色圆角底板，删除原先去除该底板的变换；裁切上沿留出
1pt 余量。四个原生 HTML 标签按各语言原稿字框定位，避免移出底板或覆盖引线。
2.3–2.5 截图直接复用已有 JE-1000H EU 英语 App 素材，字节/哈希相同，保留完整
手机顶部、状态栏和外框。未重新裁切或缩放源素材；原先截断的导出作为历史保留且不再绑定。

三语严格构建、60 个原生 PDF 哈希、源包哈希、三语冷重放通过。840/390 双宽度
检查均无标签溢出、失败图片或整页横向溢出。除上述两个 App 图外，HTML/CSS 与
preview-21 相同；46 个既有六语源文件保持不变。只做本地修正，未发布。
[素材记录](evidence/app-panel-23/asset-audit.json) ·
[验证回执](evidence/app-panel-23/validation.json) ·
[浏览器核验](evidence/app-panel-23/browser-metrics.json) ·
[灰底截图](screenshots/pt-app-panel-840-23.png) ·
[完整 App 截图](screenshots/pt-app-result-840-23.png)。

## 左侧视图顶部裁切（candidate-21）

三语左侧视图上边界由 269pt 改为 266pt，补回完整提手、机身顶边和右上角。
裁切保持在标题下方，网页标题不重复。左右、底部边界、图中标注和引线均保留。
旧可见区域仅 4–5 个抗锯齿像素有最大 3/255 的通道差异，未声称逐像素相同。
[裁切与素材记录](evidence/left-view-21/asset-audit.json) ·
[浏览器核验](evidence/left-view-21/browser-metrics.json) ·
[正文对比](evidence/left-view-21/unchanged-body.json) ·
[最终截图](screenshots/pt-left-view-840-21.png)。

三语严格构建、39 个原生 PDF 哈希及三语冷重放通过。840/390 两种宽度共 6 项
浏览器核验通过；仅左侧视图图片地址变化，其余 HTML/CSS 与 preview-19 完全一致，
第 21 行 LCD 图标及节能面板修复均保留。46 个既有六语源文件未修改。
[验证回执](evidence/left-view-21/validation.json)。

## 连接电池图标重新提取（candidate-19，后续保留）

第 21 行图标从当前原稿第 114 页的矢量重新导出。旧图为 43×34 RGB，带相邻
表格竖线；新图为 261×142 RGBA，保留电池外轮廓、内部开口及 `x8`，剔除单元格
底色和边线。三语共用这一张无本地化文字的图标；既有六语素材未修改。
PDF 保留原生矢量，PNG 以 12× 导出，已检查白底和棋盘底。

- [素材与哈希记录](evidence/lcd21-19/asset-audit.json)
- [原稿 12×](evidence/lcd21-19/source-cell-12x.png)
- [提取后棋盘底](evidence/lcd21-19/lcd-connected-batteries-checker-12x.png)
- [浏览器核验](evidence/lcd21-19/browser-metrics.json)

三语在 1280、840、390 宽度下均加载新图标，无整页横向溢出。三语严格构建与
冷重放通过；仅第 21 行图片地址变化，其他 HTML/CSS（包括节能整图）与 preview-18
完全一致，46 个既有六语源文件仍未修改。
[验证回执](evidence/lcd21-19/validation.json) ·
[正文对比](evidence/lcd21-19/unchanged-body.json) ·
[最终截图](screenshots/pt-lcd21-840-19.png)。

## 节能图外框和文字间距（candidate-18，后续保留）

三语节能图改为原稿完整面板，保留灰色圆角外框、顶部灰底说明、引线、单个时钟及
原始文字位置。裁切 `[27,228,343,375]` 包含四边；没有去底或删除图中文字。
沿用现有 ReferenceFigure 组件保留检索/读屏文本，不再追加图下操作标签和说明。
周围正文仍是 HTML；既有其他图不变。图内文字随整图缩放，手机端可放大阅读。

- [原稿面板/哈希核验](evidence/energy-panel-18/native-panel-audit.json)
- [浏览器检查](evidence/energy-panel-18/browser-metrics.json)
- [其余正文保持不变](evidence/energy-panel-18/unchanged-body.json)
- [最终葡语截图](screenshots/pt-energy-saving-final-18.png)

三语严格构建、共享组件覆盖、21 个面板 PDF 哈希、源包哈希及三语冷重放通过。
浏览器核对 1280、840、390 三种宽度共 9 项：节能图加载成功、外框完整、无额外
时钟/说明栏或横向溢出。屏外 3 张 App 图片处于正常懒加载等待状态，不计为坏图。
除节能图外三语正文 HTML 和 CSS 均与 preview-15 完全相同，46 个既有六语源文件
哈希不变。本次只改目标素材/绑定及规则说明，未改共享逻辑，未重复运行全量 unittest。
[验证回执](evidence/energy-panel-18/validation.json) ·
[冷重放](evidence/energy-panel-18/cold-replay.json) ·
[六语复核](evidence/energy-panel-18/six-language-readback.json)。

## 大图背景与配件排修正（candidate-15）

用户明确要求完整大图不要去底。已将 UPS、电池扩容、配件排、交流充电、太阳能充电、
车载充电共 6 类 × 3 语 = 18 张图改为对应语言原稿完整裁取。灰底、白色说明区、
圆角边框、虚线框、购物车徽标及印刷标注均保留；不新增渲染器或 CSS。
图内文字保留在成品图内，原生提取文字供检索/读屏使用，不再另加重复标题列。
手机端保留整图比例，需要浏览器放大阅读较小的图内字，不声明图内文字为独立 HTML。

- [三语图像浏览器对照](evidence/panels-15/browser-contact-sheet.jpg)
- [交流充电桌面截图](screenshots/pt-desktop-ac_wall_charging-15.png)
- [配件排桌面截图](screenshots/pt-desktop-battery_items-15.png)
- [手机截图](screenshots/pl-mobile-car_charging-15.png)
- [36 项浏览器检查](evidence/panels-15/browser-metrics.json)：三语、6 图、2 种宽度，
  无整页横向溢出、坏图或重复的图外标题。
- [18 图配方/哈希与 12× 对照](evidence/panels-15/native-panel-audit.json)：只有 crop，
  未使用去底/文字删除操作。规范化 PDF 渲染存在轻微色值差，未声称逐像素相同。
- [其余正文/图像完全相同](evidence/panels-15/unchanged-body.json)：去掉这 6 个参考图后，
  三语 main HTML 与 preview-09 分别完全一致；旧版时钟、提示框修复仍保留。
- [六语源文件复核](evidence/panels-15/six-language-readback.json)：46 个文件哈希不变。
- [最终包冷重放](evidence/panels-15/cold-replay.json)：阻止读取原 AI/配方后，Markdown 哈希一致。
- [正式素材导出回执](evidence/panels-15/asset-intake-receipt.json)：18 个面板与 161 页源档案。

本轮验证：三语原生构建与严格 Sphinx、8 项参考图回归、Ruff、维护性门禁、文档链接、
fixture-backed US 检查通过。全量 unittest 本轮为 4,958 tests / 697.121 秒，
OK（19 skipped）；前轮外部 JE-1000F fixture 失败本轮未复现，没有改动该 fixture。
最终的显式 captions_embedded 开关再次通过参考图回归；默认旧图外标题行为保持不变。

## 前轮可核验证据（candidate-09）

- [源包与重现命令](../../manual_sources/JE-1000H/EU/three-language/git-20260930-8bcb378f-intake/README.md)
- [组件和章节映射](evidence/component-map.json)：每语 16 章，LCD、规格、质保、App、操作表
  及所有参考图均通过共享组件覆盖门禁。
- [原生逐行核对](native-line-audit.json)：PT 722、NL 720、PL 726 行。
  唯一未匹配字串均为 LCD 图内连排数字 `18 19`，保留在编号图中，并有独立语义行 18、19。
  无未匹配的实质正文。此检查核验文本存在，不等于语言专家翻译审校。
- [内容结构检查](evidence/content-structure-checks.json)：AC1/AC2 四个开关步骤、四张规格表、
  单个节能时长、前置条件不再覆盖底图、语义正文无空字形。
- [冷重放](evidence/cold-replay.json)：三份冻结包在禁止读取原始 AI 与配方目录的条件下，
  重新生成的 Markdown 与原版 SHA-256 完全相同。
- [素材审计](evidence/asset-audit.json)、[正式 intake 回执](evidence/asset-intake-receipt.json)、
  [intake 清单](evidence/asset-intake-manifest.json)：38 个原生 PDF 导出，161 页源档案。
  所有原生导出做 12× 白底/棋盘底渲染；缩略总览和关键部位原倍率对照在 `evidence/asset-qa/`。
- [六语保持不变](evidence/six-language-unchanged.json)：起点提交下 46 个既有 JE-1000H 源文件
  逐文件字节相同，渲染器/CSS 未修改；已读取的六语发布清单见 [published_baseline.json](published_baseline.json)。
  本次没有远端写入，RTD 实页读取被 403/断连阻止，不能宣称线上验收。

## 保留的源稿问题

新源为 `JAK-UM-V1.0`，六语旧版来自不同的 EUUK V2.0 源，未升级旧语言。
PT `ON` / `Apagado`、规格三 AC 与操作两对 AC 的文字矛盾保持原样，部分商标上标在段尾。
PT 的 `12 V⎓10 A máx.` 已凭 Illustrator 原生文字和坐标恢复语义；成品概览图仍保留
PDF 字体显示限制。旧有连接电池图标的 43×34 RGB 低清/不透明底已在 candidate-19 修复；
candidate-09 的其余 63 张绑定 PNG 有真实 alpha；本轮完整面板按用户要求保留背景，
不再将透明通道作为这些大图的验收条件，未伪造提高清晰度。

## 前轮验证与交付状态（历史）

通过：三语原生导入与严格 Sphinx；共享组件门禁；正式素材 intake；内容/哈希审计；
三语冷重放；9 个针对性回归；Ruff；复杂度门禁；文档链接；`git diff --check`；
带 `--data-root tests/fixtures/phase2` 的 US 构建检查。

`python3 -m unittest`：4,957 tests，939.912 秒，2 failures、20 errors、22 skipped。
失败全部来自旧 JE-1000F 可选本地素材与旁边 AI 原稿的锁定哈希不一致。
[未修改起点代码的复现](evidence/baseline-fixture-blocker.txt) 得到同一错误：
`sibling AI original disagrees with source provenance`。未更改其他任务的临时文件或放松校验。
普通 US 构建检查因本地忽略目录缺 `Spec_Master.csv` 未通过；不能推断线上 Base 缺数据。
完整日志在 `evidence/validation/`。

上述前轮阻塞本轮未复现。本轮仍仅本地修正和提交，没有 PR、远端写入或发布。
共享适配和目标素材分别提交，现有图标/操作组件没有改动。
`docs/index.rst` 的构建副作用、生成输出和旧候选调试目录均保留，不进入任务提交。

归档测试日志中的随机 `run_key` 已替换为 `test-run-id-omitted`，防止凭据形状误报；测试结果与错误记录未改。
