# AI 修正工具包

运行环境：macOS，装有 Adobe Illustrator（应用名默认是 "Adobe Illustrator 2026"，用 `ls /Applications | grep -i illustrator` 确认），python3，并执行过 `pip install pymupdf`。

| 文件 | 用途 |
|---|---|
| `locate.py FILE.ai PAGE "文字"` | 查找某页上的文字，输出 PDF 坐标 bbox，直接拿来填 spec。另有 `--dump`（列出整页所有 span）和 `--footer`（只看页脚数字） |
| `spec2jsx.py` | 把 spec JSON 转成只含 ASCII 的 ExtendScript（非 ASCII 字符一律按 UTF-16 码点传递，避免经 osascript 桥接时乱码）。由 run_fix.sh 自动调用 |
| `apply_changes.jsx.tpl` | Illustrator 端的执行模板：按「位置 + 原文」双重校验找到文本框，再修改。对不上就记 FAIL，不会猜 |
| `run_fix.sh SRC.ai SPEC.json [--dry-run] [--app NAME]` | 复制一份 ASCII 文件名的工作副本 → 执行 → 导出改动页 PNG → 另存为 `<原名>_修正.ai` → 运行 verify。原文件不动。只要有一处 FAIL，就不保存 |
| `verify.py ORIG.ai FIXED.ai SPEC.json` | 用 PyMuPDF 独立复核：页数、每处改动的新旧文字出现次数、未改动的页是否完全一致、内嵌字体是否被降级 |

## spec 格式

```json
{
  "model": "JE-2000F", "source_name": "HTE154-EU-9国语言-0924.ai", "artboards": 170,
  "changes": [
    {"id": "footer-116", "page": 116, "op": "set", "old": "01", "new": "109",
     "pdf_bbox": [26.7, 503.8, 32.4, 510.0], "pos": {"left": 26.5}, "note": "..."},
    {"id": "fr-double", "page": 28, "op": "replace", "old": "Double to", "new": "Double jusqu'à",
     "pdf_bbox": [301.1, 386.1, 340.0, 392.0]},
    {"id": "dup-p35", "page": 35, "op": "delete_artboard"}
  ]
}
```

- `page`：1 起算的 PDF 页号，等于画板序号；永远写**原文件**的页号，删除画板后的页号偏移由工具自动处理。
- `op`：
  - `set`：整个文本框的内容必须**完全等于** `old`，再整体替换为 `new`。适用于页码、目录数字、单独一行的标题。
  - `replace`：文本框内 `old` 必须**恰好出现一次**，原地替换，保留该段第一个字符的格式。适用于长段落里的一小段。
  - `delete_artboard`：删除该画板，以及完全落在画板内的顶层对象。
- `pdf_bbox`：直接用 locate.py 输出的 bbox。工具用它的中心点去找包含该点的文本框。
- `pos`（可选）：改完后重新定位。`{"left": x}` 让左边缘对齐到 PDF 坐标 x，`{"right": x}` 让右边缘对齐。不写就保持原位。
- 在 Illustrator 里，自动换行处是一个空格。如果 `old` 跨过了手动换行（`\r`），dry-run 会报 FAIL，这时缩短 `old`。
- 已转曲（outlined）的文字 locate.py 找不到，脚本也改不了，只能交给设计师。

## 验证状态

- **已验证（Linux，无 Illustrator）：**
  - `spec2jsx.py` 生成的脚本只含 ASCII，并能通过 `node --check` 语法检查。
  - 非 ASCII 的新旧文本（如 `jusqu'à`）能正确编码成码点数组。
  - `verify.py` 用 JE-2000F 的预览 PDF 测试结果为 PASS，用未修改的原文件测试则报 FAIL，两种情况都判断正确。
  - `locate.py` 的三种模式都能正常输出。
- **尚未在真实 Illustrator 中运行过：** `apply_changes.jsx.tpl` 和 `run_fix.sh`。首次使用时，务必先跑 `--dry-run`，并逐张查看导出的 PNG。`replace` 和 `delete_artboard` 两种操作尤其需要在第一个文件上逐项人工核对。
