# 快速开始指南

Updated: 2026-04-02

本文档只保留当前仓库最常用的 happy path。
它用固定示例 `JE-1000F` 的 `US/en + US/es + US/fr + JP/ja` 说明从初稿、评审到发布的最短路径。

它不是完整命令手册，也不覆盖以下高级主题：

- 本地 listener / Feishu 事件监听
- `Document_link` 队列与回写
- GitHub Actions 自动化细节

这些内容请分别查看：

- [`hello_auto-doc.md`](hello_auto-doc.md)
- [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md)
- [`../README.md`](../README.md)

---

## 1. 示例目标

本文档统一使用以下 4 个目标：

- `US/en`
- `US/es`
- `US/fr`
- `JP/ja`

对应配置：

- [`../config.us-en.yaml`](../config.us-en.yaml)
- [`../config.us-es.yaml`](../config.us-es.yaml)
- [`../config.us-fr.yaml`](../config.us-fr.yaml)
- [`../config.ja.yaml`](../config.ja.yaml)

评审开始后，日常可编辑源通常位于：

- `docs/_review/JE-1000F/US/en/`
- `docs/_review/JE-1000F/US/es/`
- `docs/_review/JE-1000F/US/fr/`
- [`../docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

固定四语言整套导出优先使用：

- [`../scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1)
- [`../scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py)

---

## 2. 开始前

先在仓库根目录准备本地环境。

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

导出相关依赖：

- PDF 路径通常需要 `xelatex`
- 非 Word COM 的 Word 导出路径通常需要 `pandoc`

第一次在某台机器上跑 Word / PDF 前，建议先做环境自检：

```powershell
python build.py doctor --config config.us-en.yaml --model JE-1000F --region US
python build.py doctor --config config.us-es.yaml --model JE-1000F --region US
python build.py doctor --config config.us-fr.yaml --model JE-1000F --region US
python build.py doctor --config config.ja.yaml --model JE-1000F --region JP
```

如果你的数据源来自 Feishu / Lark phase2 快照，先同步：

```powershell
python build.py sync-data --config config.yaml --data-root data/phase2 --dry-run
python build.py sync-data --config config.yaml --data-root data/phase2
```

如果你不使用 `data/phase2/`，可以跳过上面这一步，并在后面的命令里去掉 `--data-root data/phase2`。

---

## 3. 先记住三层内容

### 3.1 共享种子层

包含模板和结构化数据：

- [`../docs/templates/`](../docs/templates)
- [`../data/phase2/`](../data/phase2)
- [`../data/phase1/`](../data/phase1)

用途：

- 生成第一版草稿
- 维护可复用的页面结构和参数
- 承载多个目标共享的模板逻辑

### 3.2 评审工作层

包含目标级 review bundle：

- [`../docs/_review/`](../docs/_review)

用途：

- 目标特有的日常评审修改
- Git 可追踪的评审历史
- 评审开始后的正式发布源

### 3.3 运行时输出层

包含运行时 bundle 和导出产物：

- [`../docs/_build/`](../docs/_build)

用途：

- 临时运行时 RST bundle
- 最终 HTML / Word / PDF 输出

规则只有三条：

1. 评审开始前，从模板和数据生成草稿。
2. 评审开始后，日常编辑放到 `_review`。
3. 不要把 [`../docs/_build/`](../docs/_build) 当成长期编辑面。

---

## 4. Happy Path

### 4.1 先生成运行时草稿

如果你使用 phase2 快照，推荐显式指定 `--data-root data/phase2`：

```powershell
python build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python build.py rst --config config.us-es.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python build.py rst --config config.us-fr.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime --data-root data/phase2
```

这一步的目的：

- 强制从模板和数据种子生成最新草稿
- 不把旧 `_review` 内容混回运行时草稿
- 让你先确认模板和数据层本身是通的

运行后可在以下目录看到运行时 RST：

- `docs/_build/JE-1000F/US/en/rst/`
- `docs/_build/JE-1000F/US/es/rst/`
- `docs/_build/JE-1000F/US/fr/rst/`
- `docs/_build/JE-1000F/JP/rst/`

### 4.2 初始化 Review Bundle

确认运行时草稿没问题后，为 4 个目标各自 seed 一次 review：

```powershell
python build.py review --config config.us-en.yaml --model JE-1000F --region US --data-root data/phase2
python build.py review --config config.us-es.yaml --model JE-1000F --region US --data-root data/phase2
python build.py review --config config.us-fr.yaml --model JE-1000F --region US --data-root data/phase2
python build.py review --config config.ja.yaml --model JE-1000F --region JP --data-root data/phase2
```

第一次 baseline 建议立刻入 Git：

```powershell
git add docs/_review/JE-1000F/US docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F US/JP review baseline"
```

这样后面的 `diff-report` 才有稳定比较基线。

### 4.3 进入日常评审循环

从这一步开始，默认把 `_review` 当成日常编辑源。

常见编辑面：

- `docs/_review/JE-1000F/US/en/page/*.rst`
- `docs/_review/JE-1000F/US/es/page/*.rst`
- `docs/_review/JE-1000F/US/fr/page/*.rst`
- [`../docs/_review/JE-1000F/JP/page/`](../docs/_review/JE-1000F/JP/page)

评审轮次里最常用的检查命令：

```powershell
python build.py check --config config.us-en.yaml --model JE-1000F --region US
python build.py check --config config.us-es.yaml --model JE-1000F --region US
python build.py check --config config.us-fr.yaml --model JE-1000F --region US
python build.py check --config config.ja.yaml --model JE-1000F --region JP
```

如果要从 review 内容导出 Word 预览：

```powershell
python build.py word --config config.us-en.yaml --model JE-1000F --region US --source review
python build.py word --config config.us-es.yaml --model JE-1000F --region US --source review
python build.py word --config config.us-fr.yaml --model JE-1000F --region US --source review
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

或者直接用批量脚本导出整套 review 预览：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word --source review
```

日常最短循环：

1. 修改目标自己的 `_review`
2. 运行 `check`
3. 需要时导出 `word` 或 `html`
4. `git add` 本轮真实改动
5. `git commit`
6. `git push`
7. 打开或更新 PR，让 `Review Preview Package` 生成可共享预览

### 4.4 参数变化时不要直接重刷整包 review

评审期间如果变的是共享参数或共享模板，先改共享源，再把变更同步进 `_review`。

推荐用法：

```powershell
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US --data-root data/phase2
python build.py sync-review --config config.us-es.yaml --model JE-1000F --region US --data-root data/phase2
python build.py sync-review --config config.us-fr.yaml --model JE-1000F --region US --data-root data/phase2
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --data-root data/phase2
```

适合 `sync-review` 的场景：

- `Spec_Master.csv` 等参数数据变化
- 占位符驱动页面变化
- 生成页或数据驱动页需要刷新

不建议默认使用：

```powershell
python build.py review --refresh-review ...
```

因为它的语义是“用模板和数据重新替换已有 review bundle”。
只有当你明确想整包重 seed 当前 review 时才用它。

如果你改的是纯文本模板页，而不是参数驱动页，通常更接近真实工作流的做法是：

1. 改共享模板
2. 把同样的文字调整写到对应 `_review` 页面
3. 再提交模板和 `_review`

### 4.5 导出 Revision Record

至少有两个 review 提交之后，再跑 `diff-report` 才最有意义。

最常用命令：

```powershell
python build.py diff-report --config config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-es.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-fr.yaml --model JE-1000F --region US
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
```

默认行为：

- 比较 Git ref 之间的差异，而不是工作区未提交改动
- 默认比较 `HEAD~1 -> HEAD`
- 默认忽略 baseline 首次入 Git 时的大量初始 Added 噪声

主要输出目录：

- `reports/version_tracking/JE-1000F/US/en/`
- `reports/version_tracking/JE-1000F/US/es/`
- `reports/version_tracking/JE-1000F/US/fr/`
- `reports/version_tracking/JE-1000F/JP/`

推荐打开顺序：

1. `*_index.html`
2. `*_fields.html`
3. `*_fields.csv`

### 4.6 正式发布

正式发布使用 `publish`：

```powershell
python build.py publish --config config.us-en.yaml --model JE-1000F --region US
python build.py publish --config config.us-es.yaml --model JE-1000F --region US
python build.py publish --config config.us-fr.yaml --model JE-1000F --region US
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

`publish` 会：

1. 对 review 内容跑 `check`
2. 导出 revision report
3. 从 review 构建最终 Word
4. 写 release manifest

如果你只需要 traceability record，不想重跑整个 `publish`，可以单独运行：

```powershell
python build.py release-manifest --config config.us-en.yaml --model JE-1000F --region US
python build.py release-manifest --config config.us-es.yaml --model JE-1000F --region US
python build.py release-manifest --config config.us-fr.yaml --model JE-1000F --region US
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

---

## 5. 固定四语言批量构建速查

固定矩阵 `US/en + US/es + US/fr + JP/ja` 优先用批量脚本。

一条命令构建整套 HTML / Word / PDF：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
```

构建 review 版 HTML / Word：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word --source review
```

构建完成后自动打开 HTML：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

先做 `check` 再导出：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --check-first --formats html,word,pdf
```

只跑部分语言，例如 `en + ja`：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --languages en,ja --formats html,word,pdf
```

只看将执行的命令，不真正构建：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --dry-run
```

典型 Word 输出：

- `docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx`
- `docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx`
- `docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx`
- `docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`

什么时候优先用批量脚本：

- 你要一次性导出四语言整套产物
- 你要统一验证 4 个目标是否都能生成
- 你要快速给评审或运营准备整套预览

什么时候回到单目标 `build.py`：

- 你正在编辑某一个目标的 review 内容
- 你只想跑某一个目标的 `review`、`sync-review`、`diff-report`、`publish`
- 你只需要定位一个目标的失败原因

---

## 6. 常见错误

- 把 [`../docs/_build/`](../docs/_build) 当成长期编辑面
- 运行 `review` 却以为它会自动替换现有 review 文本
- 不理解 `review --refresh-review` 会整包替换 review bundle
- 评审中改了共享参数，却忘了跑 `sync-review`
- 对目标特有评审意见继续去改共享模板
- `diff-report` 之前没有先提交 `_review` baseline
- 只改了工作区文件，还没 commit，就期待 `diff-report` 里能看到结果

---

## 7. 深入阅读

如果你需要更深的上下文，按下面顺序读：

1. [`hello_auto-doc.md`](hello_auto-doc.md)
2. [`../code-as-doc/build_doc_guide.md`](../code-as-doc/build_doc_guide.md)
3. [`../README.md`](../README.md)

适用范围：

- `hello_auto-doc.md`：当前工作流、评审层、环境边界、自动化入口
- `build_doc_guide.md`：完整命令语义和输出规则
- `README.md`：仓库入口和文档地图

---

## 8. 一句话规则

先用模板和数据 seed 草稿，再为每个目标建立 `_review` baseline；评审开始后日常编辑 `_review`，参数变化用 `sync-review`，最后按目标 `diff-report` / `publish`，固定四语言整套导出交给 `build_us_jp_manuals.ps1`。
