# 接手手册（ONBOARDING）

给下一个维护者的第一小时。这份文件的质量由**冷启动演练**保证（见 §7）：
每季度让一个没有任何背景的新人（或无记忆的 AI agent 会话）只靠仓库内文档
执行 §6 的金路径——卡住的每一步都是本文件的 bug，当天修。

其余文档不用先读。本文件读完后的下一站永远是 [`AGENTS.md`](AGENTS.md)（操作规则的单一真相）。

## 1. 这是什么系统（60 秒版）

便携储能产品说明书的 docs-as-code 流水线：飞书多维表存**产品数据**（规格/占位/脚注/
能力矩阵），本仓库存**模板与构建器**（RST → LaTeX PDF / Word / HTML / IDML），
评审者直接改飞书云文档，改动被**回写**（backport）到数据表或评审 RST——
内容永远单源，产出永远重建。

三条流转：**文档流**（规格→构建→评审→回写，闭环）、**语料流**（评审修正→翻译
记忆→预翻译，闭环）、**模板流**（模板→构建，反哺回路在建）。

## 2. 两平面拓扑（先记住这个再动手）

| 平面 | 仓库 | 职责 | 数据 |
|---|---|---|---|
| 工程面 | `Bingboom/auto-manual` | **所有代码改动只发生在这里** | 旧 base（legacy，只读） |
| 业务运行面 | `Bingboom/Hello-Docs` | 队列构建、评审分支、回写实操 | 新 base（文档构建 + TM 规范库 B）|

代码合入 auto-manual main → `sync-hello-docs.yml` 自动镜像到 Hello-Docs。
**纪律：永远不要直接改 Hello-Docs 的代码。** 详图：[`user-guide/two_plane_map.md`](user-guide/two_plane_map.md)。

## 3. 什么跑在哪（bus factor 登记表）

| 能力 | 跑在哪 | 若机器/人不可用，重建方式 |
|---|---|---|
| CI 验证（lint/unittest/check/预览包） | GitHub Actions（`manual-validation.yml` 等 9 个 workflow） | 无需重建，仓库自带 |
| 队列构建 / 评审启动 | Hello-Docs 的 Actions（`workflow_dispatch` 触发；cron 大多禁用） | secrets 见下行 |
| 飞书读写（lark-cli / 队列） | GitHub secrets（两仓各一套）+ 操作者本机 `~/.openclaw/.env`、`~/.auto-manual-phase2.env` | 在飞书开放平台重发 app 凭据 → 更新 secrets；表/视图 ID 清单在 `two_plane_map.md` §1.1 |
| InDesign 终饰（IDML→成品 PDF） | **仅操作者 Mac**（真 InDesign + `tools/idml/indesign_finalize.jsx`），不在任何 CI | **有版本锁**（`tools/idml/indesign_version_pin.json`，finalize 启动时比对、不匹配拒跑）+ 第二主机 runbook（[`code-as-doc/dev/indesign_second_host_runbook.md`](code-as-doc/dev/indesign_second_host_runbook.md)）；**待第二主机首次验证**（跑通后在 runbook §3 和本行登记日期） |
| GitHub 推送 | 操作者 gh OAuth（`gh auth login --web`） | 新维护者自己 `gh auth login` |
| TeX / pandoc | CI 镜像内置；本机需自装（`python build.py doctor` 自检） | doctor 会列出缺什么 |

## 4. 真相在哪（五个指针，别的都是派生物）

1. **产品数据**：飞书「文档构建」base 的 phase2 源表（仓库 `data/phase2/*.csv` 只是 sync-data 快照镜像）
2. **模板**：`docs/templates/`（`page_*` 按区域/语言分目录；样式单源 `tools/idml/STYLE_MAP.md` + `docs/renderers/contracts/manual_style.yaml`）
3. **操作规则**：[`AGENTS.md`](AGENTS.md)（分支/提交/验证/并行窗口纪律全在里面）
4. **路线图**：[`code-as-doc/optimization_project.md`](code-as-doc/optimization_project.md) + [`code-as-doc/next_optimization_checklist.md`](code-as-doc/next_optimization_checklist.md)
5. **运营手册**：[`user-guide/closed_loop_ops_guide.md`](user-guide/closed_loop_ops_guide.md)（回写/台账/仪表的日常操作）

生成物不是真相：`docs/_build/`、`docs/_review/generated/`、`params.tex`（由 CSV 生成）——发现它们"不对"时，修上游。

## 5. 高频命令速查

```bash
python build.py doctor                    # 本机环境自检
python -m unittest                        # 全量测试（改逻辑必跑）
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2
python tools/flow_dashboard.py report     # 双面仪表（系统健康 + 产出证明）
```

本机无飞书凭据时，构建/check 用测试夹具：`--data-root tests/fixtures/phase2`。

## 6. 金路径演练（接手考核内容）

依次完成，只许看仓库内文档：

1. **环境**：clone → `python -m venv .venv && pip install -r requirements.txt` → `build.py doctor` 全绿（或明确知道缺什么、为什么不影响下一步）
2. **构建**：用 fixtures 数据跑一次 `build.py check`（US/JE-1000F）到 `[check] OK`
3. **读懂一条产线**：说出 JE-1000F US 的 config → manifest → 模板目录 → 构建产物 的对应关系
4. **回写一轮（沙盘）**：读 `closed_loop_ops_guide.md` §1–§4，说出评审者在云文档改了一个规格值后，改动经过哪些节点回到源表、基线如何前移
5. **仪表**：跑 `flow_dashboard.py report`，解释运营面每个指标的数据源

预期用时半天。超过一天 = 文档有 bug，记录卡点并修复。

## 7. 冷启动演练协议

- **频率**：每季度一次，或每次核心维护者变更时
- **执行者**：未参与过本仓库的新人，或一个全新的、无历史记忆的 AI agent 会话
- **规则**：只准使用仓库内文档 + 公开互联网；不准问老维护者
- **产出**：卡点清单 → 当天修进对应文档 → 在 `code-as-doc/code_optimization_log.md` 记一条演练记录
- **底线指标**：金路径 §6 六步全通；通不过的版本不算"可接手"

## 8. 已知的单点与坑（接手前心里有数）

- InDesign 终饰环节无 CI，但**有版本锁**（pin 不匹配拒跑，见 §3 与 second-host runbook）；文字改动**禁止**在 InDesign 层做，必须走回写回路
- 回写对"整表/整节纯删除"是盲区——每轮回写后跑删除专项核对
- 退役产线：关源表行 `Is_Latest`，**不要删构建表行**（公式字段架构下删行=关联行悬空）
- 构建环境已锁定：CI/ReadTheDocs/队列 worker 都从 `requirements.lock` 安装（K1）；改依赖 = 改 `requirements.txt` 范围 + 按 lock 头部的步骤重生成 lock，同一 PR 提交。排版漂移由警告棘轮（I2）+ 工具链 provenance（I3）看护
- 多窗口并行开发是常态：动手前 `git status` + pull，见 `AGENTS.md` §8
