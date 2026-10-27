# 与基础版本的差异

基础版本：[`git-20261026-cc8b3421`](../../git-20261026-cc8b3421/README.md)，已发布的 JS-100I JP 包（#1611）。
原稿 PDF 与 Web 的版式差异记录见基础版本的 `source/differences.md`。除下表所列行外，那份记录对本版本仍然适用。
复制过来的 `source/`、`assets/` 文件和 `render.py` 与基础版本逐字节相同，只有下表两处不同。基础版本自己的 `source/approval.json` 和 `source/differences.md` 没有复制。

| 位置 | 基础版本 | 本版本 | 依据 |
| --- | --- | --- | --- |
| `source/page/spec_ja.rst` p10 電気データ | 声明的普通表，只用共享 `manual-spec-table`，外面包一层 `table-wrapper`，没有外框；窄屏在表内横向滚动 | 仍是声明的三列表（`shared_component_exceptions`，文字哈希不变），改用共享 `hb-spec-table-composition` 外框和 `hb-spec-label` / `hb-spec-value` 单元格类，与 HB-TABLE-SPEC 的「基本情報」「多機能アダプタ」两张表一致 | 操作员 2026-10-27 看线上页面：「这个表格样式不对吧」；随后「按新版本包发布」 |
| `source/presentation.css` | `div.table-wrapper { overflow-x: auto; }` | 表头 STC / BNPI 按原稿加粗；这张表取消最小宽度，三列在 390 px 宽内放得下、不滚动 | 只有几何和字体规则，没有颜色或边框（共享样式门禁） |

不变的部分：

- 可见文字与基础版本完全相同，`tests/test_js100i_jp_web.py` 会核对。
- 组件计数不变（HB-CALLOUT-STRIP 4、HB-SPECIAL-INBOX 1、HB-SPECIAL-REFERENCE-FIGURE 8、HB-TABLE-SPEC 2）。
- 原稿疑点照录，留给原稿负责人修正（「保留疑点后续纠正」）。
