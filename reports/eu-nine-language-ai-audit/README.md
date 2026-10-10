# EU 九语说明书 .ai 审核（2026-10-09）

审核对象：飞书「发布文档管理」多维表 `数据表`（Base `WGVwb2HctauRi7sEiKqcIzTRn1c` / 表 `tblzVaiTRVfx3x9X` / 视图 `vewQl2JaPl`）中「页码调整后」字段的 11 个 `.ai` 附件。审核全程只读，原文件和飞书表都没有改动。

| 路径 | 内容 |
|---|---|
| `audits/<型号>.md` | 每个文件一份审核报告：页脚页码、目录、语言串入、型号一致性、其他缺陷。每条带 PDF 页、页脚和原文证据，并附「已排除」的误报 |
| `manifest.tsv` | 型号 → 飞书 record_id / 附件 file_token / 原附件名 |
| `specs/JE-2000F.json` | JE-2000F 页码修正的改动清单（PT/NL/PL 页脚改为 109–162 全书连续，目录页 P7 同步），用户已确认方案 |
| `PROMPT.md` | 交给 Mac 端 agent 的提示词：依据审核报告逐个修正 `.ai` |

修正工具在 [`.claude/skills/ai-manual-pagenum-fix/scripts/`](../../.claude/skills/ai-manual-pagenum-fix/scripts/README.md)。修正必须在装有 Adobe Illustrator 的 Mac 上执行。

审核要点：

- 只有 JE-2000F 有大面积页码错误（PT/NL/PL 三段）。JS-100I 有一个整页重复的画板（p35）。其余 9 个文件的页码和目录全部正确。
- 多数问题是语言串入和规格表标签错误，详见各报告。
