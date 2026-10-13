# 本地验证

- 原稿：JA-TS02A、US/en、JAK-UM-V1.0；92 页，仅英文 PDF 3–24 / 印刷 01–22。完整原稿以三个有序二进制分片无损保存，重组 SHA-256 与原文件一致。
- 全文覆盖：英文源文本行无遗漏；五行源 PDF 文本层缺字已按实际页面恢复，记录于 source/text-recovery.json。
- 表格：符号、17 项规格、电缆、11 行 LED 状态、4 行扭矩均为原生 HTML；全部行/单元格与源数据一致。
- 32 张完整插图／App 图、4 个共用安全符号、7 个源稿内联 App 控件；图片无缺失。
- 冷重放：生成文件逐字节一致。输入图片改动被拒绝，随后完整恢复并再验全部冻结哈希。
- 严格 Sphinx：python -m sphinx -W --keep-going -b html，成功。
- Ruff：目标 build_web.py，成功。
- build.py check：JE-1000F/US、tests/fixtures/phase2，成功；仅是共用仓库回归，不证明 JA-TS02A 的 phase2／印刷构建登记。前几次失败来自稀疏检出缺少 manifests、conf、asset_promotions/asset_evidence，补齐原跟踪依赖后已通过，未改动共用代码。
- 浏览器：实际 CSS 视口 1280×900 和 390×844 均无页面或图框溢出、无缺图。手机宽表格使用内部横向滚动。最终恢复默认视口。
- 原工作区无改动。检查工具在本独立工作区自动生成了 docs/index.rst 与 JE-1000F 构建输出；这些回归工件保留且不进入目标 PR。
- 只提交 data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1/**。没有共用代码／CLI／配置／schema／工作流变更，没有在线表、队列、资产或链接字段写入。

本候选未合入、未发布；公开链接与 RTD 验收留到独立发布步骤。
