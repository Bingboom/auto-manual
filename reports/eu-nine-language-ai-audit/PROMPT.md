# 任务：依据审核报告，逐个修正 11 份 EU 说明书 .ai 文件

你在一台装有 Adobe Illustrator 的 Mac 上工作，工作目录是 auto-manual 仓库根目录。本任务用到的文件：

- `reports/eu-nine-language-ai-audit/audits/<型号>.md`：11 份只读审核报告。每条问题都写明了 PDF 页、页脚、原文证据和修改建议。
- `reports/eu-nine-language-ai-audit/manifest.tsv`：型号、飞书记录 ID、附件 file_token、原始附件名。
- `reports/eu-nine-language-ai-audit/specs/JE-2000F.json`：已经算好并核对过的 JE-2000F 改动清单，共 96 处，可以直接执行。
- `.claude/skills/ai-manual-pagenum-fix/scripts/`：locate.py / run_fix.sh / verify.py 等脚本，先读该目录下的 `README.md`。

先读 `.claude/skills/ai-manual-pagenum-fix/SKILL.md` 及其 `references/`，下面的硬规则就是从那里来的。

## 硬规则（任何情况都不能违反）

1. **原文件不改。** 输出一律是 `<原名>_修正.ai`，`run_fix.sh` 已经保证了这一点。不覆盖、不删除用户的文件。
2. **先查字体。** 在第一次用 Illustrator 保存之前，先用 PyMuPDF 列出该文件用到的全部字体（`page.get_fonts(full=True)`），逐个确认本机已安装：Gilroy 全系、SegoeUISymbol、AdobeSongStd-Light、SourceHanSansSC、FZLTZHK、HelveticaNeueLTCom-Cn、Bahnschrift 等。缺字体时，Illustrator 保存会把 ⎓ 这类特殊符号悄悄变成空白方框，即使什么都没改也会发生。缺字体就停下来告诉用户，让用户决定是先装字体还是接受风险。
3. **每个文件都先 dry-run**（`--dry-run`）。必须 `FAIL=0` 才能正式执行。遇到 FAIL 就修 spec（缩短 old、修正 bbox），不准绕过校验，也不准改成按内容模糊匹配。
4. **改完必须做两道验证：**
   - 用 Read 看 `~/Desktop/aifix_png/<型号>/` 下改动页的 PNG。
   - `verify.py` 必须输出 `RESULT: PASS`。出现字体 WARN 时，要渲染相关页并放大查看特殊符号。
   两道都过，这个文件才算完成。
5. **只做下文 A 类改动。** B 类必须先把译文提给用户、经确认后才能改；C 类只汇报，不动手。
6. **不写飞书。** 任务只是生成本地修正文件。回传附件到「内容审核后」等字段必须经用户明确确认，而且写入后要读回，报告 record_id、字段和 file_token。
7. **一次只处理一个文件。** 卡住时如实说明卡在哪里，不要用伪造或假设的结果代替。
8. **仓库改动走分支和 PR。** 新写的 spec 和 changelog 要提交进仓库，按 `AGENTS.md` §8 处理：用 `scripts/start_branch.sh` 新建分支，提 PR，不要自己合并。修正后的 `.ai` 是生产文件，不提交进仓库。

## 改动分级

- **A 类：机械、确定，可以直接做**
  - 页码、目录页码、语言区间标签。
  - 整页重复：例如 JS-100I 的 p35 和 p34 逐像素相同，删除 p35 后页码自动连续。
  - 混入的外语词句，**前提是正确文本在同一文件、同一语言里已经存在**。例如：
    - DE 段标题误写成 "PANTALLA LCD"，而 DE 目录里写的是 "LCD-ANZEIGE"。
    - NL 的 "Aan/uit-knop voor DC" 实际指 AC 键，应改为 "Aan/uit-knop voor AC"。
    - 句尾多出来的一句外语重复句，删除即可。
  - 明显的单词断开或缺字母，例如 "fonctionne ment"、"RECAUZIONI"、"UENTE DE"。
- **B 类：需要新译文**
  - 外语段落，而文件里找不到该语言的正确版本。例如 DE 段里的整段西班牙语说明、IT 段里的德语 F0–F6 处理措施。
  - 做法：对照同文件 EN 原文，必要时查翻译记忆库，给出译文方案。整理成「页 / 原文 / 建议译文」表交给用户，确认后再用 `replace` 改。
- **C 类：结构或业务问题，只汇报**
  - 内容块重复、缺失的安全条目、缺页（如 JE-2000E 的 PT/NL/PL IMPORTANT 页）、封底缺行、DoC/RED 声明。
  - 产品命名（Battery Pack 3600 是否带 Plus）、参数取值（IT 60 Hz、°F、Cycle Life 行）。
  - 已转曲的文字（locate.py 找不到）。
  - 报告里标为「待人工确认」的所有项目。

## 每个文件的流程

1. 读 `reports/eu-nine-language-ai-audit/audits/<型号>.md`，把每一条问题归入 A、B、C 类。报告里列为「已排除」的不要处理。
2. 拿到原文件。优先使用用户提供的本地路径。如需从飞书下载（只读，bot 身份）：
   - Base：`WGVwb2HctauRi7sEiKqcIzTRn1c`
   - 表：`tblzVaiTRVfx3x9X`
   - 字段：「页码调整后」
   - 记录 ID 和 file_token 见 `reports/eu-nine-language-ai-audit/manifest.tsv`。
   - 命令：`lark-cli base +record-download-attachment --as bot --base-token … --table-id … --record-id … --file-token … --output <型号>.ai`
   下载后核对文件大小，并确认 `file` 显示为 PDF 页数等于画板数。
3. 用 `.claude/skills/ai-manual-pagenum-fix/scripts/locate.py` 逐条确定 A 类改动的 bbox 和准确原文，写成 `reports/eu-nine-language-ai-audit/specs/<型号>.json`：
   - id 要能看出对应报告里的哪一条。
   - 每条都写 note。
   - `artboards` 填该文件的实际页数。
4. 把 A 类 spec 整理成表格（页 / 原文 → 新文 / 理由），连同 B 类译文方案交给用户确认。JE-2000F 的 spec 用户已确认（页码 109–162 全书连续，目录同步），可以跳过这一步。
5. 依次运行：
   - `.claude/skills/ai-manual-pagenum-fix/scripts/run_fix.sh <原文件.ai> reports/eu-nine-language-ai-audit/specs/<型号>.json --dry-run`
   - `.claude/skills/ai-manual-pagenum-fix/scripts/run_fix.sh <原文件.ai> reports/eu-nine-language-ai-audit/specs/<型号>.json`
6. 看 PNG，确认 `verify.py` 输出 PASS。另外把改动页导出或渲染出来，和原文件同页对比，确认版式没有漂移：数字宽度变化后的对齐、换行、溢出。
7. 写 `reports/eu-nine-language-ai-audit/changelogs/<型号>.md`，内容包括：每处改动（old → new）、跳过的项及原因、B/C 类遗留清单、验证结果。

建议顺序：JE-2000F（spec 已就绪）→ JS-100I（删除 p35 这一个画板）→ 其余 9 个，从 A 类最多的开始。

## Illustrator 桥接的已知坑（scripts 已处理，自己写脚本时也要遵守）

- **用 JXA 调用：** `osascript -l JavaScript` 加 `Application("Adobe Illustrator 2026").doJavascript(code)`，注意方法名是 `doJavascript`，j 小写。不要用 AppleScript 的 `do javascript`。
- **桥接只走 ASCII：** 文件路径、JSX 源码里都不能出现中文或带重音的字母。非 ASCII 字符一律在运行时用 `String.fromCharCode` 拼出来。Unicode 文件名的改名放到 shell 里用 `mv` 完成。
- **不要逐目标扫描全部 textFrames：** 先按画板一次性分桶，再在桶里查找。否则会超过 AppleEvent 的超时（-1712），Illustrator 卡死。万一卡住，用 `pkill -9 -f "Adobe Illustrator"` 结束，重新打开后从干净副本重来。
- **坐标换算：** PDF 坐标原点在左上，y 向下；Illustrator 的 y 向上。`ai_x = pdf_x + artboard.left`，`ai_y = artboard.top - pdf_y`。

## 最终交给用户

- 一张总表：型号 / 输出文件路径 / A 类已改条数 / verify 结果 / B 类待确认条数 / C 类遗留条数。
- 所有 B 类、C 类事项合并成一张清单，标明负责方（翻译 / 设计 / 业务），交给用户分派。
