# 快速开始指南

Updated: 2026-04-01

本文档描述当前仓库里一条真实可用的四语言手册工作流。
主示例使用 `JE-1000F` 的固定 4 语言集合：

- `US/en`
- `US/es`
- `US/fr`
- `JP/ja`

正式评审开始后，可编辑源通常位于：

- `docs/_review/JE-1000F/US/en/`
- `docs/_review/JE-1000F/US/es/`
- `docs/_review/JE-1000F/US/fr/`
- [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

本文档中的示例目标：

- 产品：`JE-1000F`
- 目标语言集：`US/en + US/es + US/fr + JP/ja`
- 配置：
  - [`config.us-en.yaml`](../config.us-en.yaml)
  - [`config.us-es.yaml`](../config.us-es.yaml)
  - [`config.us-fr.yaml`](../config.us-fr.yaml)
  - [`config.ja.yaml`](../config.ja.yaml)
- 最终 Word 输出：
  - [`docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx`](../docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx)
  - [`docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx`](../docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx)
  - [`docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx`](../docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx)
  - [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)
- 配置规则：批量构建优先使用 [`scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1)，单目标 review / publish / diff-report 仍然通过 `build.py` 分目标执行

---

## 1. 环境准备

开始这个四语言示例前，请先完成 [`hello_auto-doc.md`](hello_auto-doc.md) 中的环境准备。

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
  - [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
  - [`docs/templates/page_us-es/*.rst`](../docs/templates/page_us-es)
  - [`docs/templates/page_us-fr/*.rst`](../docs/templates/page_us-fr)
  - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- 结构化数据：
  - 首选快照根 [`data/phase2/`](../data/phase2)
  - [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
  - [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
  - [`data/phase2/Spec_Notes.csv`](../data/phase2/Spec_Notes.csv)
  - [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)
  - [`data/phase2/symbols_blocks.csv`](../data/phase2/symbols_blocks.csv)
  - 兼容旧基线 [`data/phase1/`](../data/phase1)
用途：

- 生成第一版草稿
- 维护可复用的共享结构
- 承载多个产品共用的模板逻辑
- 如果内容来自飞书多维表格，先运行 `python build.py sync-data --config config.yaml --data-root data/phase2`，再显式用 `--data-root data/phase2` 构建

### 2.2 评审工作层

- `docs/_review/JE-1000F/US/en/**`
- `docs/_review/JE-1000F/US/es/**`
- `docs/_review/JE-1000F/US/fr/**`
- [`docs/_review/JE-1000F/JP/**`](../docs/_review/JE-1000F/JP)

用途：

- 4 个目标各自的日常评审修改
- Git 可追踪的评审历史
- 评审开始后的正式发布源

### 2.3 运行时输出层

- [`docs/_build/JE-1000F/US/en/**`](../docs/_build/JE-1000F/US/en)
- [`docs/_build/JE-1000F/US/es/**`](../docs/_build/JE-1000F/US/es)
- [`docs/_build/JE-1000F/US/fr/**`](../docs/_build/JE-1000F/US/fr)
- [`docs/_build/JE-1000F/JP/**`](../docs/_build/JE-1000F/JP)

用途：

- 临时运行时 bundle
- 最终 HTML / Word / PDF 输出

规则：

- 评审开始前，用模板和数据生成第一版草稿
- 评审开始后，编辑对应语言自己的 `_review` 根目录
- 不要把 [`docs/_build/**`](../docs/_build) 当成编辑面

---

## 3. 你应该改哪里

### 3.1 什么时候改模板或 CSV

只有当变更应该被多个目标复用时，才去改模板或 CSV。

典型场景：

- 通用 US / JP 页面结构调整
- 可复用的标题、版式或样式改动
- 需要被多个机型复用的新占位符族
- [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) 中真实参数更新

### 3.2 日常手册生产时改 `_review`

一旦某个语言目标进入评审，日常文案修改应该放在它自己的 `_review` 根目录里，例如：

- `docs/_review/JE-1000F/US/en/page/*.rst`
- `docs/_review/JE-1000F/US/es/page/*.rst`
- `docs/_review/JE-1000F/US/fr/page/*.rst`
- [`docs/_review/JE-1000F/JP/page/*.rst`](../docs/_review/JE-1000F/JP/page)

适用场景：

- 当前目标特有的措辞调整
- 评审意见处理
- 临时发布用修订
- 最终发布前润色

### 3.3 评审期资源覆盖

如果评审期需要替换图片，请放到：

- `docs/_review/JE-1000F/US/en/overrides/_static/**`
- `docs/_review/JE-1000F/US/es/overrides/_static/**`
- `docs/_review/JE-1000F/US/fr/overrides/_static/**`
- [`docs/_review/JE-1000F/JP/overrides/_static/**`](../docs/_review/JE-1000F/JP/overrides/_static)

并保持与公共资源相同的相对路径。

只有下面这几类 override 会叠加到运行时 bundle：

- `docs/_review/JE-1000F/<region>/<lang>/overrides/_static/**`
- `docs/_review/JE-1000F/<region>/<lang>/overrides/_assets/**`
- `docs/_review/JE-1000F/<region>/<lang>/overrides/renderers/**`
- JP 目标对应的是 [`docs/_review/JE-1000F/JP/overrides/**`](../docs/_review/JE-1000F/JP/overrides)

---

## 4. 端到端流程

对 `JE-1000F` 的 4 语言集合来说，真实流程是：

1. 用模板和数据创建或更新 4 个语言目标的草稿种子
2. 创建独立评审分支
3. 初始化 4 个目标各自的 review bundle
4. 在整个评审周期内持续编辑各自的 `_review`
5. 对 4 个目标的评审内容运行 `check`
6. 每轮评审都 commit 并 push
7. 打开或更新 PR
8. 让 `Review Preview Package` 在 Vercel 上托管 4 语言评审预览
9. 按目标导出 revision record
10. 按目标正式发布，或用批量脚本导出整套 HTML / Word / PDF

---

## 5. 阶段 A：从模板和数据生成第一版草稿

第一次在某台机器上跑 Word / PDF 前，建议先跑一次环境自检：

```powershell
python build.py doctor --config config.us-en.yaml --model JE-1000F --region US
python build.py doctor --config config.us-es.yaml --model JE-1000F --region US
python build.py doctor --config config.us-fr.yaml --model JE-1000F --region US
python build.py doctor --config config.ja.yaml --model JE-1000F --region JP
```

它会告诉你当前机器是否具备：

- 当前 `word_source` 所需的 Word 导出条件
- 当前 `pdf.mode` 所需的 PDF 导出条件
- 需要的 Python 模块
- 需要的系统工具，比如 Word COM、`pandoc`、`xelatex`

如果你使用飞书多维表格作为内容治理层，先同步冻结快照：

```powershell
python build.py sync-data --config config.yaml --data-root data/phase2 --dry-run
python build.py sync-data --config config.yaml --data-root data/phase2
```

如果你同时用飞书 `Document_link` 表做本机构建任务队列，也可以在同步后直接消费 `是否触发文档构建 = Y` 的任务并把生成的 Word 路径回写到 `Document directory`：

```powershell
python build.py process-build-queue --config config.yaml --data-root data/phase2
```

这一步会先把 `开始构建时间` 写回到任务行，再构建本地 Word、上传到飞书 Drive、把上传后的文件自动 move 到当前知识库容器、把本机路径写回 `Document directory`，并把知识库里的链接写回 `Document link`；成功后会把 `是否触发文档构建` 回写为 `已构建`。
如果任务行还带了 `Git_ref`，队列会先 fetch 这个分支并在临时 worktree 里构建，再把产物回拷到当前仓库的 `docs/_build` 后上传；这样 Draft / Publish 都能沿用同一条 review / PR 分支，而不会悄悄退回 `main`。
如果你想让这张表自动轮询 `Y` 任务，Windows 侧直接调 [`../scripts/process_build_queue.ps1`](../scripts/process_build_queue.ps1) 会比直接调 Python 命令更稳，因为它会补齐 `.venv`、Node/npm 和保存到用户环境变量里的 `FEISHU_PHASE2_*`。
如果你想改成“勾选后立即构建”而不是轮询，给 `Document_link` 表增加 checkbox 字段 `是否立即构建`，在飞书开放平台里为当前自建应用添加并发布 `drive.file.bitable_record_changed_v1` 事件，然后启动 [`../scripts/listen_build_queue.ps1`](../scripts/listen_build_queue.ps1)；监听器会用当前登录用户身份订阅这张表的云文档事件，并在对应记录被勾选时立刻触发本地构建。
如果你想完全脱离本机，可以改用远端仓库里的 [`../.github/workflows/feishu-build-queue.yml`](../.github/workflows/feishu-build-queue.yml)；它会在默认分支上每 5 分钟轮询一次 Feishu 队列，也支持 `workflow_dispatch`。
如果你想让远端仓库“立即构建”，就在飞书里新建一个工作流，条件设成 `是否触发文档构建 = Y` 且 `是否立即构建 = 选中`，动作改成调用 GitHub 的 `workflow_dispatch` API 去触发 `feishu-build-queue.yml`。队列处理器本身仍然只把 `是否触发文档构建 = Y` 的行视为待构建任务，`是否立即构建` 只是决定要不要立刻唤起 GitHub Actions。
这条远端链路要额外准备 GitHub Secrets：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、所有 `FEISHU_PHASE2_*` 表/视图 ID；同时还要确保这个 Feishu app/bot 对 phase2 源表有读取权限、对 `Document_link` 表有写回权限。

这一步需要额外配置 `FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID` 和 `FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID`，并复用同一个 `FEISHU_PHASE2_BASE_TOKEN`；如果你要强制改成别的知识库父节点，再额外设置 `FEISHU_PHASE2_DOCUMENT_LINK_WIKI_PARENT_TOKEN`。

如果你希望远程 GitHub Actions 也把上传后的 Word 自动 move 到知识库里，还要确保当前飞书应用/机器人对目标知识库父节点有编辑权限；否则会出现“上传成功，但 move 失败”。

然后再从模板和数据准备运行时草稿：

```powershell
python build.py rst --config config.us-en.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python build.py rst --config config.us-es.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python build.py rst --config config.us-fr.yaml --model JE-1000F --region US --source runtime --data-root data/phase2
python build.py rst --config config.ja.yaml --model JE-1000F --region JP --source runtime --data-root data/phase2
```

这个命令会：

- 读取对应语言的模板：
  - [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)
  - [`docs/templates/page_us-es/*.rst`](../docs/templates/page_us-es)
  - [`docs/templates/page_us-fr/*.rst`](../docs/templates/page_us-fr)
  - [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- 读取当前选定快照根里的 [`Spec_Master.csv`](../data/phase2/Spec_Master.csv) 和其他 CSV
- 生成 CSV 驱动页面
- 输出运行时草稿到：
  - [`docs/_build/JE-1000F/US/en/rst/`](../docs/_build/JE-1000F/US/en/rst)
  - [`docs/_build/JE-1000F/US/es/rst/`](../docs/_build/JE-1000F/US/es/rst)
  - [`docs/_build/JE-1000F/US/fr/rst/`](../docs/_build/JE-1000F/US/fr/rst)
  - [`docs/_build/JE-1000F/JP/rst/`](../docs/_build/JE-1000F/JP/rst)

这里特意使用 `--source runtime`，原因是：

- 它保证草稿来自模板和数据种子
- 不会把旧 `_review` 内容重新带进来

---

## 6. 阶段 B：第一次初始化 Review

草稿准备好后，如果要进入正式评审，就 seed review bundle：

```powershell
python build.py review --config config.us-en.yaml --model JE-1000F --region US
python build.py review --config config.us-es.yaml --model JE-1000F --region US
python build.py review --config config.us-fr.yaml --model JE-1000F --region US
python build.py review --config config.ja.yaml --model JE-1000F --region JP
```

这个命令会：

1. 从模板和数据生成一份新的运行时草稿
2. 把可评审子集复制到：
   - `docs/_review/JE-1000F/US/en/`
   - `docs/_review/JE-1000F/US/es/`
   - `docs/_review/JE-1000F/US/fr/`
   - [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

重要行为：

- 如果对应的 review 根目录不存在，就创建它
- 如果它已经存在，`review` 默认保留现有 review 内容
- 这样可以避免误覆盖评审修改

只有在你明确要丢掉当前 review 文本、重新从模板和数据 seed 时，才用 `--refresh-review`：

```powershell
python build.py review --config config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py review --config config.us-es.yaml --model JE-1000F --region US --refresh-review
python build.py review --config config.us-fr.yaml --model JE-1000F --region US --refresh-review
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

---

## 7. 阶段 C：编辑 Review Bundle

评审开始后，正常编辑面就是：

- `docs/_review/JE-1000F/US/en/**`
- `docs/_review/JE-1000F/US/es/**`
- `docs/_review/JE-1000F/US/fr/**`
- [`docs/_review/JE-1000F/JP/**`](../docs/_review/JE-1000F/JP)

这是最关键的工作流切换：

- 不要继续在语言模板目录里做目标特有的日常评审改动
- 不要继续改 [`docs/_build/**`](../docs/_build) 里的运行时产物
- 要持续编辑对应语言自己的 `_review`

如果后面发现某个变更其实应该被多个产品共享，再单独把逻辑回迁到模板或数据层。

---

## 8. 阶段 D：对 Review 内容跑质量门禁

`check` 默认使用 `source=auto`。
这意味着：

- 如果 review bundle 存在，`check` 会校验 review 内容
- 如果 review bundle 不存在，`check` 会校验模板和数据生成的 runtime 草稿

运行：

```powershell
python build.py check --config config.us-en.yaml --model JE-1000F --region US --data-root data/phase2
python build.py check --config config.us-es.yaml --model JE-1000F --region US --data-root data/phase2
python build.py check --config config.us-fr.yaml --model JE-1000F --region US --data-root data/phase2
python build.py check --config config.ja.yaml --model JE-1000F --region JP --data-root data/phase2
```

它会检查：

- 目标身份
- 脏的外部型号名
- 未解析占位符
- 缺失 include 目标
- 缺失资源
- 页面 contract 中的占位符、spec key、page-value selector 和资源

---

## 9. 阶段 E：从 Review 构建预览产物

评审开始后，构建命令默认用 `source=auto`。
如果对应语言的 `_review` 存在，review 内容会先叠加到 runtime bundle 再导出。

如果你要一次性构建 4 语言预览产物，直接运行：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf --source review
```

如果你想写得更明确，可以显式指定 review：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats word --source review
```

如果你临时想忽略 review，只看模板和数据输出：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats word --source runtime
```

如果你只想看某一页的独立预览，不改标准 runtime bundle，也要按 4 个目标分别执行。例如 `00_preface`：

```powershell
python build.py preview --config config.us-en.yaml --model JE-1000F --region US --page 00_preface
python build.py preview --config config.us-es.yaml --model JE-1000F --region US --page 00_preface
python build.py preview --config config.us-fr.yaml --model JE-1000F --region US --page 00_preface
python build.py preview --config config.ja.yaml --model JE-1000F --region JP --page 00_preface
```

它们会写到各自的 preview 目录里，例如：

- [`docs/_build/JE-1000F/US/en/preview/00_preface/rst/`](../docs/_build/JE-1000F/US/en/preview/00_preface/rst)
- [`docs/_build/JE-1000F/US/es/preview/00_preface/rst/`](../docs/_build/JE-1000F/US/es/preview/00_preface/rst)
- [`docs/_build/JE-1000F/US/fr/preview/00_preface/rst/`](../docs/_build/JE-1000F/US/fr/preview/00_preface/rst)
- [`docs/_build/JE-1000F/JP/preview/00_preface/rst/`](../docs/_build/JE-1000F/JP/preview/00_preface/rst)

如果你只是想要一份新的 runtime draft，方便调模板或占位符：

```powershell
python build.py fast --config config.us-en.yaml --model JE-1000F --region US
python build.py fast --config config.us-es.yaml --model JE-1000F --region US
python build.py fast --config config.us-fr.yaml --model JE-1000F --region US
python build.py fast --config config.ja.yaml --model JE-1000F --region JP
```

如果你需要给设计评审看的托管预览，使用专门的 review preview packager。
当前 Vercel 入口仍以 `US/en` config 为主，但生成的 manual 站点会带上这 4 个语言入口：

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
git switch -c codex/review-je1000f-multilang
```

之后 JE-1000F 这 4 个语言目标的评审都在这个分支上继续推进。
如果后面还有更多评审轮次，就继续往同一个分支 push，并保持 PR 打开，直到整条线可以合并。

每一轮有意义的评审修改都应该提交。

先判断你这一轮改动属于哪一类：

1. 只改目标特有 review 文本  
   直接改 `docs/_review/**`，然后只提交 `_review`
2. 改参数 CSV，或者改“带占位符”的共享模板页  
   先改共享源，再用 `sync-review` 把变更写进 `_review`，最后一起提交
3. 改“纯文本”的共享模板页  
   先改 `docs/templates/**`，再手动把对应改动写进 `docs/_review/**`；只有在你明确接受覆盖当前 review 文本时，才用 `review --refresh-review`

推荐：

```powershell
git add docs/_review/JE-1000F/US docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F US/JP manuals"
```

如果这一轮还改了共享模板或共享数据：

```powershell
git add data/phase2 docs/templates docs/_review/JE-1000F/US docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F US/JP manuals"
```

规则：

- commit 当前这一轮真实的编辑源
- 目标特有改动通常只需要 `_review`
- 共享改动需要模板或数据与 `_review` 一起提交
- 但前提是：你必须先把共享改动真正同步进 `_review`；只改 `docs/templates/**` 或 `data/phase2/**` 然后直接 `git add`，不会自动让已进入 review 的文档显示出这次变更
- 如果这一轮实际只动了几张页面，更推荐 `git add` 具体文件，不要无脑 `git add docs/_review/JE-1000F/US docs/_review/JE-1000F/JP`

提交后 push 分支并打开或更新 PR：

```powershell
git push -u origin codex/review-je1000f-multilang
```

当前托管 review-preview 的流程是：

1. 先按需从模板和数据生成草稿
2. 用 `python build.py review --config ...` 初始化 `_review`
3. 在 `docs/_review/<model>/US/<lang>/` 或 [`docs/_review/<model>/JP/`](../docs/_review) 下编辑 review bundle
4. commit 并 push 评审分支
5. 创建或更新 PR
6. `Review Preview Package` 打包 review HTML、Word handoff、diff-report HTML、diff CSV 和 Excel workbook
7. 工作流把这个静态包部署到 Vercel，并在有权限时把预览链接评论到 PR

如果还没有打开 PR，或者你需要手动重建预览，可以在 push 后去 `Actions -> Review Preview Package` 手动运行。

### 10.1 Review 阶段速查表

| 你改了什么 | 正确操作 | 不该怎么做 |
| --- | --- | --- |
| `_review` 里的目标特有文案 | 直接提交 `docs/_review/**` | 不要回头改 `docs/templates/**` 期待它自动进 review |
| `Spec_Master.csv` / `Spec_Footnotes.csv` / `spec_titles.csv` | 先跑 `sync-review`，再提交共享源和 `_review` | 不要只提交 phase2 CSV，不同步 `_review` |
| 带占位符的共享模板页 | 先跑 `sync-review`，确认对应 review 页已更新，再提交 | 不要假设所有模板页都会自动同步 |
| 纯文本共享模板页 | 手动把同样修改写进 `docs/_review/**`，再一起提交 | 不要只改模板；这样 preview / diff-report 往往看不到 |
| 明确要用新的共享种子层整包覆盖评审稿 | 用 `review --refresh-review` | 不要在不确定影响时直接 refresh 整包 |

---

## 11. 阶段 G：评审中参数发生变化怎么办

如果评审已经开始，而你又修改了：

- [`data/phase2/Spec_Master.csv`](../data/phase2/Spec_Master.csv)
- [`data/phase2/Spec_Footnotes.csv`](../data/phase2/Spec_Footnotes.csv)
- [`data/phase2/spec_titles.csv`](../data/phase2/spec_titles.csv)

默认不要用 `--refresh-review`。

应该用：

```powershell
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US
python build.py sync-review --config config.us-es.yaml --model JE-1000F --region US
python build.py sync-review --config config.us-fr.yaml --model JE-1000F --region US
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP
```

如果 Windows 提示 `docs/_build/...` 被浏览器、Word、资源管理器或 PDF 预览占用，先关闭这些窗口；如果你只是想在现有输出上继续同步，可以直接补 `--no-clean`：

```powershell
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US --no-clean
python build.py sync-review --config config.us-es.yaml --model JE-1000F --region US --no-clean
python build.py sync-review --config config.us-fr.yaml --model JE-1000F --region US --no-clean
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --no-clean
```

默认行为：

- 先从模板和数据重建 runtime draft
- 再把参数驱动的文件同步进各自语言的 `_review` 根目录
- 普通人工改过的 review 页面保持不动

默认同步的文件包括：

- `generated/**/*.rst`
- `page/spec_*.rst`
- `page/safety_*.rst`
- 任何源模板里带有占位符的页面，比如 `|PRODUCT_NAME|` 或 `|MAIN_POWER_BUTTON_LABEL|`
- 由标题或产品身份生成的 cover 页面

重要边界：

- `sync-review` 适合“参数驱动”或“带占位符的模板页”
- 如果你改的是共享模板里的普通说明文字，而这个 review 页面已经不再由 `sync-review` 自动覆盖，那么变更不会自动体现在 `_review`
- 这类改动要么手动改对应的 `_review` 页面，要么在你明确接受覆盖当前 review 文本时使用 `review --refresh-review`

例如：

- 改 [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) 里的规格参数 -> 用 `sync-review`
- 改 [`docs/templates/page_us-en/05_operation_guide_placeholder.rst`](../docs/templates/page_us-en/05_operation_guide_placeholder.rst) 里带 `|PRODUCT_NAME|` 这类占位符的段落 -> 通常可以用 `sync-review`
- 改 [`docs/templates/page_us-en/00_preface.rst`](../docs/templates/page_us-en/00_preface.rst) 这种纯文本模板内容 -> 如果 review 里对应页面没有被 `sync-review` 自动覆盖，就需要手动把改动写进 `docs/_review/...`

如果你只想同步 spec 和 generated 草稿文件：

```powershell
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US --sync-scope generated
python build.py sync-review --config config.us-es.yaml --model JE-1000F --region US --sync-scope generated
python build.py sync-review --config config.us-fr.yaml --model JE-1000F --region US --sync-scope generated
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --sync-scope generated
```

进入 review 之后，`check`、`html`、`word`、`pdf`、`publish` 在真正构建前也会自动执行同样的参数同步。
这一步现在只刷新参数驱动的行，不会把整张 review 页面整页覆盖掉。
US 英文 review 现在只认 `docs/_review/<model>/US/en/`，旧的 `docs/_review/<model>/US/page/**` 已经退休，不再被构建读取。

固定 `safety_*.rst` 页面不在这个 `generated` 范围里；如果你改的是 safety 模板，改完后请直接同步对应页，例如：

```powershell
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US --page-file safety_en.rst
python build.py sync-review --config config.us-es.yaml --model JE-1000F --region US --page-file safety_es.rst
python build.py sync-review --config config.us-fr.yaml --model JE-1000F --region US --page-file safety_fr.rst
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file safety_ja.rst
```

同样，如果碰到 Windows 文件锁，也可以补 `--no-clean`。

如果某一张普通 review 页面也要从 runtime 替换回来：

```powershell
python build.py sync-review --config config.us-en.yaml --model JE-1000F --region US --page-file 02_whats_in_the_box.rst
python build.py sync-review --config config.us-es.yaml --model JE-1000F --region US --page-file 02_whats_in_the_box.rst
python build.py sync-review --config config.us-fr.yaml --model JE-1000F --region US --page-file 02_whats_in_the_box.rst
python build.py sync-review --config config.ja.yaml --model JE-1000F --region JP --page-file 02_whats_in_the_box.rst
```

这一招只适合“你希望用 runtime 重新覆盖 review 的那一页”。  
如果你改的是纯文本模板页，而 runtime 并不会自动给你产出新的 review 页面内容，那么还是要手动改 `docs/_review/**`。

只有在你明确要整包重新 seed 时，才使用 `review --refresh-review`。

如果一个 config 里同时声明了多个目标和多语言，也支持批量 refresh：

```powershell
python build.py sync-review --config config.yaml
```

---

## 12. 阶段 H：Baseline 与普通评审轮次

### 12.1 第一次 baseline

```powershell
python build.py review --config config.us-en.yaml --model JE-1000F --region US
python build.py review --config config.us-es.yaml --model JE-1000F --region US
python build.py review --config config.us-fr.yaml --model JE-1000F --region US
python build.py review --config config.ja.yaml --model JE-1000F --region JP
git add docs/_review/JE-1000F/US docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F US/JP review baseline"
```

### 12.2 普通后续轮次

```powershell
python build.py check --config config.us-en.yaml --model JE-1000F --region US --data-root data/phase2
python build.py check --config config.us-es.yaml --model JE-1000F --region US --data-root data/phase2
python build.py check --config config.us-fr.yaml --model JE-1000F --region US --data-root data/phase2
python build.py check --config config.ja.yaml --model JE-1000F --region JP --data-root data/phase2
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats word --source review
git add docs/_review/JE-1000F/US docs/_review/JE-1000F/JP
git commit -m "Update JE-1000F US/JP manuals"
```

如果这一轮还改了共享模板或共享数据，正确顺序是：

1. 先改共享源：
   - `data/phase2/**`
   - `docs/templates/**`
2. 再决定怎么把变更写进 `_review`：
   - 参数或占位符页：优先用 `sync-review`
   - 纯文本模板页：直接手动修改对应的 `_review` 页面
   - 只有在明确要整包替换 review 文本时，才用 `review --refresh-review`
3. 最后一起提交共享源和 `_review`

更贴近日常评审的推荐顺序：

1. 先改共享源或 review 文本
2. 如果是参数页或占位符页，运行 `sync-review`
3. 如果是纯文本模板页，直接把同样修改写进对应 `_review` 页面
4. 跑 `check`
5. 只 `git add` 这轮实际改动过的文件
6. commit 并 push

如果你明确要整包 review 草稿从头刷新：

```powershell
python build.py review --config config.us-en.yaml --model JE-1000F --region US --refresh-review
python build.py review --config config.us-es.yaml --model JE-1000F --region US --refresh-review
python build.py review --config config.us-fr.yaml --model JE-1000F --region US --refresh-review
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review
```

这个操作只能在你明确知道自己在替换当前 review 文本时使用。

如果你只是修正某一张纯文本 review 页面，更接近真实工作流的做法是：

```powershell
git add docs/templates/page_us-en/00_preface.rst
git add docs/_review/JE-1000F/US/en/page/00_preface.rst
git commit -m "Update US preface wording for JE-1000F review"
```

上面这个例子就是“模板不是自动同步源”的典型情况：

- 改了 [`docs/templates/page_us-en/00_preface.rst`](../docs/templates/page_us-en/00_preface.rst)
- review 中真正用于 diff-report / preview 的是对应的 `docs/_review/**/page/00_preface.rst`
- 所以必须把 `_review` 一起改掉，变更才会体现在 review 产物里

---

## 13. 阶段 I：导出 Revision Record

至少存在两个 review 提交之后，再导出 revision report。

默认情况下，`diff-report` 已经会忽略“初稿 baseline 首次入 Git”带来的整包 Added 噪声。  
所以日常最短命令就是：

```powershell
python build.py diff-report --config config.us-en.yaml --model JE-1000F --region US
```

如果你反而想把 baseline 首次导入时的 Added 全都看出来，再显式加：

```powershell
--include-initial-adds
```

这个开关适合：

- `_review` baseline 刚进 Git，下一轮你只想看真实修改
- 当前 tracked root 在旧提交里不存在，新提交里是整包 Added
- 你要回头排查“初稿首次导入时到底带了哪些文件和字段”

推荐命令：

```powershell
python build.py diff-report --config config.us-en.yaml --model JE-1000F --region US --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.us-es.yaml --model JE-1000F --region US --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.us-fr.yaml --model JE-1000F --region US --from-ref HEAD~1 --to-ref HEAD
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP --from-ref HEAD~1 --to-ref HEAD
```

如果这是第一次 baseline，而且你不想在 report 里看到整包 Added：

```powershell
python build.py diff-report --config config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-es.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-fr.yaml --model JE-1000F --region US
python build.py diff-report --config config.ja.yaml --model JE-1000F --region JP
```

主要输出目录：

- [`reports/version_tracking/JE-1000F/US/en/`](../reports/version_tracking/JE-1000F/US/en)
- [`reports/version_tracking/JE-1000F/US/es/`](../reports/version_tracking/JE-1000F/US/es)
- [`reports/version_tracking/JE-1000F/US/fr/`](../reports/version_tracking/JE-1000F/US/fr)
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

而且它看的对象是当前目标对应的 tracked root，4 语言示例里通常是：

- `docs/_review/JE-1000F/US/en/`
- `docs/_review/JE-1000F/US/es/`
- `docs/_review/JE-1000F/US/fr/`
- [`docs/_review/JE-1000F/JP/`](../docs/_review/JE-1000F/JP)

如果 tracked root 在这两个提交之间没有 Git 差异，report 就会显示 0。

### 13.2 为什么 report 可能显示 0

最常见原因有三个：

1. 你改的是工作区文件，但还没 commit
2. 你 refresh 了 `_review`，但 `_review` 还是未跟踪 `??`
3. 你在比较 `HEAD~1 -> HEAD`，但这两个提交之间根本没有当前 tracked root 的变化

排查时优先看：

```powershell
git status --short docs/_review/JE-1000F
git diff --stat HEAD~1 HEAD -- docs/_review/JE-1000F
git diff --stat -- docs/_review/JE-1000F
```

### 13.3 模板改动怎么进入 reviewer change report

如果你改的是模板，比如：

- [`docs/templates/page_us-en/00_preface.rst`](../docs/templates/page_us-en/00_preface.rst)
- [`docs/templates/page_us-es/00_preface.rst`](../docs/templates/page_us-es/00_preface.rst)
- [`docs/templates/page_us-fr/00_preface.rst`](../docs/templates/page_us-fr/00_preface.rst)
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
python build.py review --config config.us-en.yaml --model JE-1000F --region US --refresh-review --no-clean
python build.py review --config config.us-es.yaml --model JE-1000F --region US --refresh-review --no-clean
python build.py review --config config.us-fr.yaml --model JE-1000F --region US --refresh-review --no-clean
python build.py review --config config.ja.yaml --model JE-1000F --region JP --refresh-review --no-clean
git add docs/templates/page_us-en/00_preface.rst docs/templates/page_us-es/00_preface.rst docs/templates/page_us-fr/00_preface.rst docs/templates/page_jp/00_preface.rst docs/_review/JE-1000F/US/en/page/00_preface.rst docs/_review/JE-1000F/US/es/page/00_preface.rst docs/_review/JE-1000F/US/fr/page/00_preface.rst docs/_review/JE-1000F/JP/page/00_preface.rst
git commit -m "Fix JE-1000F preface important styling"
python build.py diff-report --config config.us-en.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-es.yaml --model JE-1000F --region US
python build.py diff-report --config config.us-fr.yaml --model JE-1000F --region US
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
git add docs/_review/JE-1000F/US docs/_review/JE-1000F/JP
git commit -m "Add JE-1000F US/JP review baseline"
```

然后下一轮再提交模板和 `_review` 变化，`HEAD~1 -> HEAD` 才会干净地体现真正的页面修改。

---

## 14. 阶段 J：正式发布

`publish` 是正式发布命令。

```powershell
python build.py publish --config config.us-en.yaml --model JE-1000F --region US
python build.py publish --config config.us-es.yaml --model JE-1000F --region US
python build.py publish --config config.us-fr.yaml --model JE-1000F --region US
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

它会：

1. 对每个目标的 review 内容运行 `check`
2. 从各自的 `_review` 根目录导出 diff report
3. 从 review 构建最终 Word
4. 把 release manifest 写到各自的 release 目录

如果你是通过 `Document_link` 的 Publish 任务触发远端正式构建，记得让 `Git_ref` 保持指向当前 review / PR 分支；队列现在会按这条分支构建最终 Word，而不是回到 `main` 重新出一份不一致的成品。

`publish` 默认使用的 diff 输出目录：

- [`reports/version_tracking/JE-1000F/US/en/`](../reports/version_tracking/JE-1000F/US/en)
- [`reports/version_tracking/JE-1000F/US/es/`](../reports/version_tracking/JE-1000F/US/es)
- [`reports/version_tracking/JE-1000F/US/fr/`](../reports/version_tracking/JE-1000F/US/fr)
- [`reports/version_tracking/JE-1000F/JP/`](../reports/version_tracking/JE-1000F/JP)

如果 review bundle 不存在，`publish` 会失败。
这是刻意设计的，因为正式发布不应该静默回退到模板草稿。

如果你只需要 traceability record，而不想重跑整个 `publish`：

```powershell
python build.py release-manifest --config config.us-en.yaml --model JE-1000F --region US
python build.py release-manifest --config config.us-es.yaml --model JE-1000F --region US
python build.py release-manifest --config config.us-fr.yaml --model JE-1000F --region US
python build.py release-manifest --config config.ja.yaml --model JE-1000F --region JP
```

---

## 15. 阶段 K：单独构建最终 Word

如果你只需要 Word 文件，而不想跑完整发布流程，也可以直接运行：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats word --source review
```

它默认会使用最终 review 内容，因为：

- `build_us_jp_manuals.ps1` 会把 `--source review` 透传给每个语言目标
- 对应语言存在 `_review` 时，会优先使用最终 review 内容

如果你想写得更明确：

```powershell
python build.py word --config config.us-en.yaml --model JE-1000F --region US --source review
python build.py word --config config.us-es.yaml --model JE-1000F --region US --source review
python build.py word --config config.us-fr.yaml --model JE-1000F --region US --source review
python build.py word --config config.ja.yaml --model JE-1000F --region JP --source review
```

预期输出：

- [`docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx`](../docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx)
- [`docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx`](../docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx)
- [`docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx`](../docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx)
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

## 17. `JE-1000F` 四语言完整构建示例

这一节对应固定的 4 个语言目标：

- `US/en`
- `US/es`
- `US/fr`
- `JP/ja`

推荐直接使用批量脚本：

- PowerShell 入口：[`scripts/build_us_jp_manuals.ps1`](../scripts/build_us_jp_manuals.ps1)
- Python 实现：[`scripts/build_us_jp_manuals.py`](../scripts/build_us_jp_manuals.py)

它会自动分别调用下面这些配置：

- `US/en` -> [`config.us-en.yaml`](../config.us-en.yaml)
- `US/es` -> [`config.us-es.yaml`](../config.us-es.yaml)
- `US/fr` -> [`config.us-fr.yaml`](../config.us-fr.yaml)
- `JP/ja` -> [`config.ja.yaml`](../config.ja.yaml)

### 17.1 一条命令构建 4 语言的 HTML、Word、PDF

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word,pdf
```

这条命令会依次构建：

- `US/en`
- `US/es`
- `US/fr`
- `JP/ja`

生成完成后，典型输出路径如下：

- HTML
  - [`docs/_build/JE-1000F/US/en/html/index.html`](../docs/_build/JE-1000F/US/en/html/index.html)
  - [`docs/_build/JE-1000F/US/es/html/index.html`](../docs/_build/JE-1000F/US/es/html/index.html)
  - [`docs/_build/JE-1000F/US/fr/html/index.html`](../docs/_build/JE-1000F/US/fr/html/index.html)
  - [`docs/_build/JE-1000F/JP/html/index.html`](../docs/_build/JE-1000F/JP/html/index.html)
- Word
  - [`docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx`](../docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx)
  - [`docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx`](../docs/_build/JE-1000F/US/es/word/manual_je1000f_us_es.docx)
  - [`docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx`](../docs/_build/JE-1000F/US/fr/word/manual_je1000f_us_fr.docx)
  - [`docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx`](../docs/_build/JE-1000F/JP/word/manual_je1000f_jp.docx)
- PDF
  - [`docs/_build/JE-1000F/US/en/pdf/manual_je1000f_us_en.pdf`](../docs/_build/JE-1000F/US/en/pdf/manual_je1000f_us_en.pdf)
  - [`docs/_build/JE-1000F/US/es/pdf/manual_je1000f_us_es.pdf`](../docs/_build/JE-1000F/US/es/pdf/manual_je1000f_us_es.pdf)
  - [`docs/_build/JE-1000F/US/fr/pdf/manual_je1000f_us_fr.pdf`](../docs/_build/JE-1000F/US/fr/pdf/manual_je1000f_us_fr.pdf)
  - [`docs/_build/JE-1000F/JP/pdf/manual_je1000f_jp.pdf`](../docs/_build/JE-1000F/JP/pdf/manual_je1000f_jp.pdf)

### 17.2 常用批量构建变体

只导出 HTML 和 Word：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html,word
```

只构建部分语言，例如 `US/en` 和 `JP/ja`：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --languages en,ja --formats html,word,pdf
```

先做 `check` 再导出：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --check-first --formats html,word,pdf
```

避免清理旧产物，适合本地反复调样式或调试：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --no-clean --formats html,word
```

只预览将要执行的命令，不真正构建：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --dry-run
```

### 17.3 构建完成后直接打开多语言 HTML

如果你只关心 HTML 预览，可以在构建完成后自动打开 4 个语言的首页：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --formats html --open-html
```

如果只想打开部分语言，可以配合 `--languages` 使用：

```powershell
.\scripts\build_us_jp_manuals.ps1 --model JE-1000F --languages en,ja --formats html --open-html
```

### 17.4 什么时候用批量脚本，什么时候回到单目标流程

推荐用批量脚本的场景：

- 需要一次性导出 `US/en + US/es + US/fr + JP/ja`
- 需要统一验证 4 个语言的 HTML / Word / PDF 是否都能成功产出
- 需要快速给评审、运营或本地验收同事准备整套多语言产物

推荐继续使用单目标 `build.py` 流程的场景：

- 你正在编辑某一个目标的 review 内容
- 你只想对某一个目标执行 `review`、`sync-review`、`publish`
- 你需要生成该目标的 `diff-report`

例如 4 语言评审工作流里，单目标操作通常按目标分别执行：

```powershell
python build.py check --config config.us-en.yaml --model JE-1000F --region US
python build.py check --config config.us-es.yaml --model JE-1000F --region US
python build.py check --config config.us-fr.yaml --model JE-1000F --region US
python build.py check --config config.ja.yaml --model JE-1000F --region JP
python build.py publish --config config.us-en.yaml --model JE-1000F --region US
python build.py publish --config config.us-es.yaml --model JE-1000F --region US
python build.py publish --config config.us-fr.yaml --model JE-1000F --region US
python build.py publish --config config.ja.yaml --model JE-1000F --region JP
```

---

## 18. 常见错误

- 改 [`docs/_build/JE-1000F/US/en/rst/**`](../docs/_build/JE-1000F/US/en/rst) 或 [`docs/_build/JE-1000F/JP/rst/**`](../docs/_build/JE-1000F/JP/rst) 并期待这些改动能保留下来
- 运行 `python build.py review` 却误以为它一定会刷新 review 内容
- 运行 `python build.py review --refresh-review` 却没意识到它会替换当前 review 文本
- 评审中改了 [`Spec_Master.csv`](../data/phase1/Spec_Master.csv) 却忘了跑 `sync-review`
- 对目标特有评审意见还继续改 [`docs/templates/page_us-en/*.rst`](../docs/templates/page_us-en)、[`docs/templates/page_us-es/*.rst`](../docs/templates/page_us-es)、[`docs/templates/page_us-fr/*.rst`](../docs/templates/page_us-fr) 或 [`docs/templates/page_jp/*.rst`](../docs/templates/page_jp)
- 从 `_build` 而不是 `_review` 导出 diff report
- 评审存在后忘了 `word/html/pdf/check` 默认会优先使用 review 内容
- 在第一次 review baseline 还没入 Git 前就期待 `diff-report` 给出正常 reviewer 变更记录

---

## 19. 一句话规则

对 `JE-1000F` 的 4 语言集合来说，正确流程是：

先从模板和数据给 `US/en + US/es + US/fr + JP/ja` seed 一次 -> 分目标 `review` 一次 -> 持续编辑各自的 `_review` -> 参数变化时对对应目标运行 `sync-review` -> commit -> 按目标 `publish` 或批量导出 -> `push`
## Draft / Publish Queue Split

- `process-build-queue` now refreshes `data/phase2` before the build starts.
- `Doc_phase=Draft` is intended for PR-driven review documents.
- `Doc_phase=Publish` is intended for `main`-driven publish documents.
- `feishu-draft-build-queue.yml` should be dispatched with the PR head branch as GitHub `ref`.
- `feishu-build-queue.yml` should consume only Publish rows from `main`.
