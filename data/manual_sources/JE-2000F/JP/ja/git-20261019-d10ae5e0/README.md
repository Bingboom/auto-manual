# JE-2000F 日本国内版 Web 审阅稿

按用户 2026-10-19 的要求，走 Git-only，将指定 PDF 转为日文网页版，并参考仓库 JE-1000F 日规版的章节结构。用户尚未批准本候选的源码/素材验收、合入或上线。`publication_eligible` 保持 false。

## 源文件身份

- 产品：Jackery ポータブル電源 2000 New。封面型号：JE-2000F / JE-2000F-SG / JE-2000F-WH。JP / 日本語，国内専用。
- 原件 28 页，6,805,723 bytes；封面可见 V2。文件名 V2.0-2026-06-24 的日期仅作为文件名修订标识，不冒充正文印刷日期。
- SHA-256：`d10ae5e04ad48907538f5cf18f3afa964ac261fceb40684b6fc1ee0963003e95`。
- 原始 PDF 无改写，按字节分为 `source/pdf-archive/part-*.bin`，拼接后恢复原件；单块哈希见 `source/pdf-identity.json`。
- Web 正文是物理页 3–26 的 13 章。封面/印刷目录留在归档；目录改为 Web 导航；物理页 27 为空白，页 28 重复 App 下载信息。

## 内容和结构

安全上のご注意 → 使用上のご注意 → 免責事項 → 同梱品 → 各部の名称 → 液晶画面 → 使い方 → UPS 機能 → 充電方法 → トラブルシューティング → 主な仕様 → 保証について → Jackeryアプリ ユーザーマニュアル。

所有日文、参数、警告、保证条款、插座/接线图及 App UI 均绑定本次 JE-2000F 原稿，不导入 JE-1000F 的参数/机身/UI。指定参考为 `manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed`，哈希固定的共用图标、按钮和通用配件图保持字节一致。采用当前共享主题和组件，不复制参考版历史私有样式，不新增单型号配置或共享渲染器。

- `source/component-map.md`：印刷块到共享组件的映射。
- `source/native-pages.json`、`source/line-ledger.json`：完整原生文字、坐标及每行用途；`source/unmapped.json` 必须为空。
- `source/artwork-recipes.json`、`source/extracted-artwork.json`、`source/reused-assets.json`：提取前的候选盘点/决定、实际边界/处理与复用哈希。
- `source/ja/content.json`：可编辑语义流；`web/ja/manual.ir.json`：共享 IR；正文和表格保持可选文本。
- `source_manifest.json`：源输入、共用依赖和 Web 文件的完整哈希清单。

源稿 LCD 有 25 个编号位置、26 条说明：编号 22 共用高温/低温两条说明；保留该对应关系。能量阈值表无专用共享组件，声明为一个普通原生表（含合并默认设置单元格），不添加私有配色/边框。原稿 App 步骤 2.1 的图形加号用共享 `HB-SPECIAL-APP` 行内加号恢复；其他规范化仅合并印刷断行、生成网页列表/标题及移除印刷页码。原稿文字瑕疵不擅自润色。App 两条连接方法保留在“備考”内的子列表中。

## 重建与验证

从仓库根目录执行，输出目录须不存在：

```sh
P=data/manual_sources/JE-2000F/JP/ja/git-20261019-d10ae5e0
python3 "$P/rebuild.py" --output .tmp/je2000f-jp-cold
python3 -m sphinx -W --keep-going -b html .tmp/je2000f-jp-cold .tmp/je2000f-jp-html
python3 "$P/verify.py" --html-root .tmp/je2000f-jp-html
```

`verify.py` 重新打开归档 PDF 比对每页文字，检查源文逐行覆盖、网页可见文字、App 备注嵌套、图标复用字节、共享样式、资源闭包，并比较冷录入/冷回放结果。`validation/report.json` 保存本次结果。

已通过：严格 Sphinx 构建、源文覆盖/冷回放/共享样式/素材完整性校验、30 项相关数据与样式测试、JE-1000F/JP 家族回归（离线 phase2 fixtures，仅证明既有日规链路，无 Feishu 读写）。

桌面 1280 / 窄屏 390 的浏览器视觉验收未完成：浏览器工具无法验证管理员策略，拒绝 localhost 导航，未绕过限制。素材裸图已对照原稿检查四边，但这不等同于浏览器视觉验收。

## Git-only 边界

不读写飞书/Base、源表、构建队列、`HTML_link`、在线资产注册表或发布目录；不改共享代码、既有产品/语言包或印刷模板。仅新增本候选和必要的 Git 冻结包登记。登记引用的是用户转换请求，明确不构成合入/发布许可。工程 PR、Hello-Docs 和 RTD 发布均需按各自边界审阅，当前未合入、未上线。
