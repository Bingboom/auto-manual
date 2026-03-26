# 快速开始指南

Updated: 2026-03-26

本文档描述当前仓库里一条真实可用的手册工作流。
主示例仍然使用 `manual_je1000f_jp`，并假设正式评审开始后，可编辑源位于 [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)。

本文档中的示例目标：

- 产品：`JE-1000F`
- 区域：`JP`
- 配置：[`config.ja.yaml`](../config.ja.yaml)
- 最终 Word 输出：[`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)
- 配置规则：使用 JP 模板族配置，再通过 `--model` 和 `--region` 指定目标

---

## 1. 环境准备

开始这个 JP 示例前，请先完成 [`hello_auto-doc.md`](hello_auto-doc.md) 中的环境准备。

仓库根目录下的最小环境要求：

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

另外还要确保当前导出路径依赖的外部工具已安装。
例如完整的 PDF 路径通常需要 `xelatex`，Word 备用路径通常需要 `pandoc`。
完整环境说明请看 [`hello_auto-doc.md`](hello_auto-doc.md)。

如果你需要固定的四语言打包 `US/en + US/es + US/fr + JP/ja`，可以直接运行：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

---

## 2. 真实工作流中的三层内容

这套系统里有三层内容，它们用途不同，不要混用。

### 2.1 模板与数据种子层

- 模板：
  - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- 结构化数据：
  - [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
  - [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
  - [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)
  - [`data/phase1/content_blocks.csv`](../data/phase1/content_blocks.csv)

用途：

- 生成第一版草稿
- 维护可复用的共享结构
- 承载多个产品共用的模板逻辑

### 2.2 评审工作层

- [`docs/_review/JE-1000F/JP/index.rst`](../docs/_review/JE-1000F/JP/index.rst)
- [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)
- [`docs/_review/JE-1000F/JP/generated/JE-1000F/*.rst`](../docs/_review/JE-1000F/JP/generated/JE-1000F)
- [`docs/_review/JE-1000F/JP/overrides/**`](../docs/_review/JE-1000F/JP/overrides)

用途：

- 这个目标的日常评审修改
- Git 可追踪的评审历史
- 评审开始后的正式发布源

### 2.3 运行时输出层

- [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP)
- [`docs/_build/JE-1000F/JP/html/**`](../docs/_build/JE-1000F/JP)
- [`docs/_build/JE-1000F/JP/word/**`](../docs/_build/JE-1000F/JP/word)
- [`docs/_build/JE-1000F/JP/pdf/**`](../docs/_build/JE-1000F/JP/pdf)

用途：

- 临时运行时 bundle
- 最终 HTML / Word / PDF 输出

规则：

- 评审开始前，用模板和数据生成第一版草稿
- 评审开始后，编辑 [`docs/_review/JE-1000F/JP/**`](../docs/_review/JE-1000F/JP)
- 不要把 [`docs/_build/**`](../docs/_build) 当成编辑面

---

## 3. 你应该改哪里

### 3.1 什么时候改模板或 CSV

只有当变更应该被多个产品复用时，才去改 [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp) 或 CSV。

典型场景：

- 通用 JP 页面结构调整
- 可复用的标题、版式或样式改动
- 需要被多个机型复用的新占位符族
- [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) 中真实参数更新

### 3.2 日常手册生产时改 `_review`

一旦 `JE-1000F / JP` 进入评审，日常文案修改应该放在：

- [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)
- [`docs/_review/JE-1000F/JP/generated/JE-1000F/*.rst`](../docs/_review/JE-1000F/JP/generated/JE-1000F)

适用场景：

- 当前目标特有的措辞调整
- 评审意见处理
- 临时发布用修订
- 最终发布前润色

### 3.3 评审期资源覆盖

如果评审期需要替换图片，请放到：

- [`docs/_review/JE-1000F/JP/overrides/_static/**`](../docs/_review/JE-1000F/JP/overrides/_static)

并保持与公共资源相同的相对路径。

只有下面这几类 override 会叠加到运行时 bundle：

- [`docs/_review/JE-1000F/JP/overrides/_static/**`](../docs/_review/JE-1000F/JP/overrides/_static)
- [`docs/_review/JE-1000F/JP/overrides/_assets/**`](../docs/_review/JE-1000F/JP/overrides/_assets)
- [`docs/_review/JE-1000F/JP/overrides/renderers/**`](../docs/_review/JE-1000F/JP/overrides/renderers)

---

## 4. 端到端流程

对 `manual_je1000f_jp` 来说，真实流程是：

1. 用模板和数据创建或更新草稿种子
2. 创建独立评审分支
3. 初始化评审 bundle 一次
4. 在整个评审周期内持续编辑 `_review`
5. 对评审内容运行 `check`
6. 每轮评审都 commit 并 push
7. 打开或更新 PR
8. 让 `Review Preview Package` 在 Vercel 上托管评审预览
9. 导出 revision record
10. 从 review 正式发布

---

## 5. 阶段 A：从模板和数据生成第一版草稿

第一次在某台机器上跑 Word / PDF 前，建议先跑一次环境自检：

```powershell
python build.py doctor --config config.ja.yaml --model JE-1000F --region JP
```

它会告诉你当前机器是否具备：

- 当前 `word_source` 所需的 Word 导出条件
- 当前 `pdf.mode` 所需的 PDF 导出条件
- 需要的 Python 模块
- 需要的系统工具，比如 Word COM、`pandoc`、`xelatex`

如果这个目标还没进入 review，就先从模板和数据准备运行时草稿：

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
```

这个命令会：

- 读取 [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- 读取 [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) 和其他 CSV
- 生成 CSV 驱动页面
- 输出运行时草稿到：
  - [`docs/_build/JE-1000F/JP/rst/`](../docs/_build/JE-1000F/JP/rst)

这里特意使用 `--source runtime`，原因是：

- 它保证草稿来自模板和数据种子
- 不会把旧 `_review` 内容重新带进来

---

## 6. 阶段 B：第一次初始化 Review

草稿准备好后，如果要进入正式评审，就 seed review bundle：

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
```

这个命令会：

1. 从模板和数据生成一份新的运行时草稿
2. 把可评审子集复制到：
   - [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

重要行为：

- 如果 [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP) 不存在，就创建它
- 如果它已经存在，`review` 默认保留现有 review 内容
- 这样可以避免误覆盖评审修改

只有在你明确要丢掉当前 review 文本、重新从模板和数据 seed 时，才用 `--refresh-review`：

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

---

## 7. 阶段 C：编辑 Review Bundle

评审开始后，正常编辑面就是：

- [`docs/_review/JE-1000F/JP/index.rst`](../docs/_review/JE-1000F/JP/index.rst)
- [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)
- [`docs/_review/JE-1000F/JP/generated/JE-1000F/*.rst`](../docs/_review/JE-1000F/JP/generated/JE-1000F)

这是最关键的工作流切换：

- 不要继续在 [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp) 里做 JE-1000F JP 的日常评审改动
- 不要继续改 [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP/rst)
- 要持续编辑 [`docs/_review/JE-1000F/JP/**`](../docs/_review/JE-1000F/JP)

如果后面发现某个变更其实应该被多个产品共享，再单独把逻辑回迁到模板或数据层。

---

## 8. 阶段 D：对 Review 内容跑质量门禁

`check` 默认使用 `source=auto`。
这意味着：

- 如果 review bundle 存在，`check` 会校验 review 内容
- 如果 review bundle 不存在，`check` 会校验模板和数据生成的 runtime 草稿

运行：

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
```

它会检查：

- 目标身份
- 脏的外部型号名
- 未解析占位符
- 缺失 include 目标
- 缺失资源
- 页面 contract 中的占位符、spec key、`tpl_*` key 和资源

---

## 9. 阶段 E：从 Review 构建预览产物

评审开始后，构建命令默认用 `source=auto`。
如果 [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP) 存在，review 内容会先叠加到 runtime bundle 再导出。

因此这些命令默认都会优先使用 review：

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP
python build.py html --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
python build.py pdf --config config.ja.yaml --model JE-1000F --region JP
```

如果你想写得更明确，可以显式指定 review：

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

如果你临时想忽略 review，只看模板和数据输出：

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source runtime
```

如果你只想看某一页的独立预览，不改标准 runtime bundle：

```powershell
python build.py preview --config config.ja.yaml --model JE-1000F --region JP --page 03_product_overview_placeholder
```

它会写到：

- [`docs/_build/JE-1000F/JP/preview/03_product_overview_placeholder/rst/`](../docs/_build/JE-1000F/JP/preview/03_product_overview_placeholder/rst)

如果你只是想要一份新的 runtime draft，方便调模板或占位符：

```powershell
python build.py fast --config config.ja.yaml --model JE-1000F --region JP
```

如果你需要给设计评审看的托管预览，使用专门的 review preview packager。
当前第一阶段托管示例是 `JE-1000F / US`：

```powershell
python tools/process_docs/build_review_preview.py --config config.us-en.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

输出目录：

- [`site/review-preview/dist/`](../site/review-preview/dist)

这个 summary 页现在刻意保持极简，只作为以下入口：

- `Open Review HTML`
- `Download Word`
- `Download Change Workbook`
- `Doc Information`

详细的 page / field / file diff 不应该继续堆到 summary 页里，而应该从 summary 页跳去 change report。

---

## 10. 阶段 F：每一轮 Review 都要 Commit

在第一轮评审前，先为这条手册线创建独立分支。

推荐：

```powershell
git switch main
git pull
git switch -c codex/review-je1000f-jp
```

之后 JE-1000F JP 的评审都在这个分支上继续推进。
如果后面还有更多评审轮次，就继续往同一个分支 push，并保持 PR 打开，直到整条线可以合并。

每一轮有意义的评审修改都应该提交。

推荐：

```powershell
git add docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
```

如果这一轮还改了共享模板或共享数据：

```powershell
git add data/phase1 docs/templates docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
```

规则：

- commit 当前这一轮真实的编辑源
- 目标特有改动通常只需要 `_review`
- 共享改动需要模板或数据与 `_review` 一起提交

提交后 push 分支并打开或更新 PR：

```powershell
git push -u origin codex/review-je1000f-jp
```

当前托管 review-preview 的流程是：

1. 先按需从模板和数据生成草稿
2. 用 `python build.py review --config ...` 初始化 `_review`
3. 在 [`docs/_review/<model>/<region>/`](../docs/_review) 下编辑 review bundle
4. commit 并 push 评审分支
5. 创建或更新 PR
6. `Review Preview Package` 打包 review HTML、Word handoff、diff-report HTML、diff CSV 和 Excel workbook
7. 工作流把这个静态包部署到 Vercel，并在有权限时把预览链接评论到 PR

如果还没有打开 PR，或者你需要手动重建预览，可以在 push 后去 `Actions -> Review Preview Package` 手动运行。

---

## 11. 阶段 G：评审中参数发生变化怎么办

如果评审已经开始，而你又修改了：

- [`data/phase1/Spec_Master.csv`](../data/phase1/Spec_Master.csv)
- [`data/phase1/Spec_Footnotes.csv`](../data/phase1/Spec_Footnotes.csv)
- [`data/phase1/spec_titles.csv`](../data/phase1/spec_titles.csv)

默认不要用 `--refresh-review`。

应该用：

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

默认行为：

- 先从模板和数据重建 runtime draft
- 再把参数驱动的文件同步进 [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)
- 普通人工改过的 review 页面保持不动

默认同步的文件包括：

- `generated/**/*.rst`
- `page/spec_*.rst`
- `page/safety_*.rst`
- 任何源模板里带有占位符的页面，比如 `|PRODUCT_NAME|` 或 `|MAIN_POWER_BUTTON_LABEL|`
- 由标题或产品身份生成的 cover 页面

如果你只想同步 spec / safety 生成文件：

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
```

如果某一张普通 review 页面也要从 runtime 替换回来：

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

只有在你明确要整包重新 seed 时，才使用 `review --refresh-review`。

如果一个 config 里同时声明了多个目标和多语言，也支持批量 refresh：

```powershell
python build.py sync-review --config config.yaml
```

---

## 12. 阶段 H：Baseline 与普通评审轮次

### 12.1 第一次 baseline

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F JP review baseline"
```

### 12.2 普通后续轮次

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py word --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
```

如果你改了共享模板或共享数据，并且希望整包 review 草稿从头刷新：

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

这个操作只能在你明确知道自己在替换当前 review 文本时使用。

---

## 13. 阶段 I：导出 Revision Record

至少存在两个 review 提交之后，再导出 revision report。

推荐命令：

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
```

如果这是第一次 baseline，而且你不想在 report 里看到整包 Added：

```powershell
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD --ignore-initial-adds
```

主要输出目录：

- [`reports/version_tracking/JE-1000F/JP/`](../reports/version_tracking/JE-1000F/JP)

推荐打开顺序：

1. `*_index.html`
2. `*_fields.html`
3. `*_fields.csv`

对日常 revision sheet 来说，`*_fields.csv` 往往最适合发出去。

### 13.1 `diff-report` 比较的是什么

`diff-report` 比较的是 Git ref 之间的差异，不是你当前工作区里的未提交改动。

默认情况下，它比较的是：

- `HEAD~1`
- `HEAD`

而且它看的对象是当前目标对应的 tracked root，通常是：

- [`docs/_review/<model>/<region>/`](../docs/_review)

如果 tracked root 在这两个提交之间没有 Git 差异，report 就会显示 0。

### 13.2 为什么 report 可能显示 0

最常见原因有三个：

1. 你改的是工作区文件，但还没 commit
2. 你 refresh 了 `_review`，但 `_review` 还是未跟踪 `??`
3. 你在比较 `HEAD~1 -> HEAD`，但这两个提交之间根本没有当前 tracked root 的变化

排查时优先看：

```powershell
git status --short docs/_review/JE-1000F/JP
git diff --stat HEAD~1 HEAD -- docs/_review/JE-1000F/JP
git diff --stat -- docs/_review/JE-1000F/JP
```

### 13.3 模板改动怎么进入 reviewer change report

如果你改的是模板，比如：

- [`docs/templates/page_jp/00_preface.rst`](../docs/templates/page_jp/00_preface.rst)

那么模板文件本身不会自动出现在 reviewer change report 里。
要让它进入 reviewer change report，必须让这次变更先落到 `_review`，再通过 Git commit 形成 ref diff。

最短流程是：

1. 改模板
2. 用 `review --refresh-review` 或合适的同步手段把变更写进 `_review`
3. `git add` 并 `git commit` 对应的 `_review`
4. 再运行 `diff-report`

示例：

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review --no-clean
git add docs/templates/page_jp/00_preface.rst docs/_review/JE-1000F/JP/page/00_preface.rst
git commit -m "Fix JP preface important styling"
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
```

### 13.4 如果 `_review` 还是首次出现

如果某个语言级 review root 是第一次出现，比如新加的：

- [`docs/_review/JE-1000F/US/en/`](../docs/_review)

那么它通常会先表现为整包 `??`。
这时直接跑 `diff-report`，很可能会看到 0，因为 Git ref 里还没有它。

正确顺序是：

1. 先把 `_review` baseline 提交进 Git
2. 再做下一轮实际内容改动
3. 再跑 `diff-report`

也就是：

```powershell
git add docs/_review/JE-1000F/US/en
git commit -m "Add US/en review baseline"
```

然后下一轮再提交模板和 `_review` 变化，`HEAD~1 -> HEAD` 才会干净地体现真正的页面修改。

---

## 14. 阶段 J：正式发布

`publish` 是正式发布命令。

```powershell
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

它会：

1. 对 review 内容运行 `check`
2. 从 [`docs/_review/JE-1000F/JP`](../docs/_review/JE-1000F/JP) 导出 diff report
3. 从 review 构建最终 Word
4. 把 release manifest 写到 [`reports/releases/JE-1000F/JP/`](../reports/releases/JE-1000F/JP)

`publish` 默认使用的 diff 输出目录：

- [`reports/version_tracking/JE-1000F/JP/`](../reports/version_tracking/JE-1000F/JP)

如果 review bundle 不存在，`publish` 会失败。
这是刻意设计的，因为正式发布不应该静默回退到模板草稿。

如果你只需要 traceability record，而不想重跑整个 `publish`：

```powershell
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

---

## 15. 阶段 K：单独构建最终 Word

如果你只需要 Word 文件，而不想跑完整发布流程，也可以直接运行：

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP
```

它默认会使用最终 review 内容，因为：

- `word` 默认走 `--source auto`
- `auto` 在 review 存在时优先用 [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

如果你想写得更明确：

```powershell
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

预期输出：

- [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)

---

## 16. 阶段 L：归档与推送

你的 review bundle 本身就是可归档、可持续编辑的源。

推荐的收尾顺序：

1. commit 最终 review 内容
2. 导出 revision record
3. 从 review 构建最终 Word
4. push

命令：

```powershell
git push
```

---

## 17. `manual_je1000f_jp` 完整示例

### 17.1 首次初始化

```powershell
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime
python build.py review --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F JP review baseline"
```

### 17.2 普通评审循环

```powershell
python build.py check --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F JP manual"
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
git push
```

### 17.3 评审中参数变化

```powershell
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
git add data/phase1 docs/_review/JE-1000F/JP
git commit -m "Sync JE-1000F JP parameter updates"
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

### 17.4 有意从模板和数据重新 seed

```powershell
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

只有在你明确决定用新的共享种子层替换当前 review 文本时，才这样做。

---

## 18. 常见错误

- 改 [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP/rst) 并期待这些改动能保留下来
- 运行 `python build.py review` 却误以为它一定会刷新 review 内容
- 运行 `python build.py review --refresh-review` 却没意识到它会替换当前 review 文本
- 评审中改了 [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) 却忘了跑 `sync-review`
- 对目标特有评审意见还继续改 [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- 从 `_build` 而不是 `_review` 导出 diff report
- 评审存在后忘了 `word/html/pdf/check` 默认会优先使用 review 内容
- 在第一次 review baseline 还没入 Git 前就期待 `diff-report` 给出正常 reviewer 变更记录

---

## 19. 一句话规则

对 `manual_je1000f_jp` 来说，正确流程是：

先从模板和数据 seed 一次 -> `review` 一次 -> 持续编辑 `_review` -> 参数变化时用 `sync-review` -> commit -> `publish` -> `push`
