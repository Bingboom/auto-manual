# Codex 脚手架与仓库架构审计

更新时间：2026-07-10
基线：`origin/main`（隔离 worktree：`refactor/codex-scaffolding`）

## 结论摘要

仓库已经完成一轮有纪律的可维护性拆分：`build.py` 是兼容性入口，构建、队列、回写、校验、差异报告和 IDML 都有独立模块；长期架构也明确分成治理、快照、页面组装、构建渲染、发布追溯五层。当前总体可维护性为“中上，但配置/代理发现面存在高风险断点”：代码边界已有文档和 31 个热点守护，但 `tools/` 仍有 284 个 Python 文件，且 Codex 不会自动读取 Claude 的目录级导航与项目 skill。

## 架构地图

```text
Feishu/Lark / phase2 snapshot
          │
          ▼
  build.py + build_* entry adapters
          │
          ├── docs/templates + docs/manifests
          ├── tools/csv_pages + generated-page assembly
          ├── tools/check_* quality gates
          ├── docs/_review (review source after review starts)
          └── docs/_build (generated runtime/export bundle)
                    │
                    ▼
        HTML / Word / PDF / Markdown / IDML
                    │
                    ▼
       diff-report / release-manifest / queue writeback

OpenClaw / Feishu / DingTalk JS adapters remain outside the Python build plane.
```

### 入口与编排

- `build.py` 负责 CLI 兼容面和顶层路由，实际实现分布在 `tools/build_main.py`、`build_cli.py`、`build_dispatch.py`、`build_entry_commands.py`、`build_runtime.py`、`build_publish.py` 和 `build_reports.py`。
- `code-as-doc/dev/orchestration_module_map.md` 是当前模块归属地图，约束入口文件保持 orchestration-first。
- `tools/` 下的队列、回写、云文档 backport、Spec Master、Word/HTML/IDML 导出均有 façade/helper 拆分，测试继续依赖兼容入口。

### 内容与构建

- `data/phase2/` 是可复现的本地结构化快照；`docs/templates/` 和 `docs/manifests/` 是共享模板/页面组装层。
- `docs/_review/` 在 review 开始后成为持久编辑源；`docs/_build/` 仅是生成物。
- `tools/csv_pages/`、generated-page helpers 和 page contracts 将表格/符号/规格等结构化内容转成页面 RST，再由 Sphinx/Word/PDF/IDML 渲染。

### 集成与发布

- `integrations/openclaw/` 负责 JS 控制层和 Feishu IM ingress，与 Python 执行平面分离。
- queue workflow 负责状态推进、构建、云文档/制品回写；`diff-report` 和 `release-manifest` 提供审阅与发布追溯。

## 可维护性评估

### 做得好的地方

1. **入口兼容性明确**：入口 façade 保留测试/外部调用的导出名，降低拆分回归风险。
2. **路径和配置集中**：`tools/utils/path_utils.py` 与 `tools/build_paths.py` 避免低层模块继续硬编码输出目录和模型默认值。
3. **源与生成物分离**：`AGENTS.md`、业务逻辑文档和 `System Evolution Strategy.md` 对 `_review`、`_build`、快照和模板的 source-of-truth 规则一致。
4. **守护与验证成体系**：热点文件有行数守护；CI 覆盖 Ruff、mypy、单测、文档链接、质量门和集成测试。
5. **边界有活文档**：编排模块地图、业务逻辑总览和优化路线图能解释“代码应放在哪里”。

### 风险（按优先级）

#### P0：Codex 发现面不完整

仓库原本有根级 `AGENTS.md`，但 11 个目录级说明只有 `CLAUDE.md`；Codex 因而无法获得 `tools/`、`docs/`、`configs/`、`tests/` 等目录的局部边界和验证命令。Claude 的 `config-review` 与 `hardcore-task-execution` 也只在 `.claude/skills/`，不符合 Codex skill 必须有 `name` 的 frontmatter。适配保留 `.claude/` 原入口，不让 Claude 改用 Codex 副本。

#### P1：skill 元数据不齐

原有 11 个 `.agents/skills` 中只有 8 个带 `agents/openai.yaml`；缺失 UI/默认 prompt 的 skill 仍可被文件发现，但不会稳定出现在 Codex 的 skill 绑定面。迁移后应保持 `SKILL.md` 与 `agents/openai.yaml` 一一对应。

#### P1：配置说明存在双轨漂移

`.claude/` 的 README 明确区分 Claude project skills 和 `.agents/skills`。根 `AGENTS.md` 现在分别保留 Claude 与 Codex 的配置审查入口，避免任一运行时被重定向到另一套 skill。

#### P1：文档仍有旧分支命名

部分用户指南示例使用 `codex/<topic>`，而仓库并行开发规则明确禁止以 agent 身份作为分支前缀，要求使用 `feat/`、`fix/`、`refactor/`、`docs/` 等变更类型前缀。

#### P2：工具平面仍然很宽

`tools/` 有约 284 个 Python 文件、约 73k 行；最大热点包括 `queue_query.py`（1200 行）、`spec_master_rebuild.py`（1147 行）、`word_bundle_docx_styles.py`（1044 行）和 `cloud_doc_backport_orchestration.py`（934 行）。现有守护能阻止继续膨胀，但下一阶段应继续以领域 façade、输入/输出 contract 和边界测试降低跨模块认知负担。

#### P2：双层导航有重复维护成本

保留 Claude 的 `CLAUDE.md` 与新增 Codex 的 `AGENTS.md` 会产生同步成本。当前内容是稳定的目录地图，短期可接受；后续应避免在两份文件中新增不同规则，所有政策继续只放根 `AGENTS.md`。

## 基线验证

- `python3 tools/check_maintainability_guardrails.py`：31 个热点全部通过。
- `python3 -m ruff check build.py integrations tools tests scripts`：通过。
- `python3 tools/check_doc_link_integrity.py`：68 个 Markdown 文件、1305 条链接、0 个断链。

## 建议

本次适配只处理代理发现与文档一致性，不改构建行为、数据 schema、CLI 签名或依赖版本。代码层面的下一步应继续沿现有 `orchestration_module_map.md` 和热点守护推进，优先围绕 queue/backport/spec-master 的 contract 测试和跨模块依赖收敛。
