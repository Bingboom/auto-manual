# Codex 脚手架适配计划

## 目标

把 Claude 项目配置中已经验证过的导航和工作方法转换成 Codex 可发现、可触发、可验证的 repo-local surface，同时不改变 manual build、review、queue、snapshot 或 release 行为。

## 阶段

### Phase 1：发现与基线（完成）

- 盘点根/目录级 `CLAUDE.md`、`AGENTS.md`、`.claude`、`.agents/skills` 和 `.codexignore`。
- 读取 `build.py`、编排模块地图、系统演进策略、业务逻辑总览和可维护性守护。
- 运行 Ruff、文档链接和热点守护基线。

### Phase 2：Codex skill 迁移（完成）

- 将 Claude 的 `config-review` 与 `hardcore-task-execution` 转为 `.agents/skills/` 下的 Codex skill。
- 将 Claude 的 `references/recipes.md` 保留为 Codex skill 的按需参考资料。
- 为迁移 skill 和原先缺失元数据的三个本地 skill 补充 `agents/openai.yaml`。
- 不删除 `.claude/`，保证 Claude Code 兼容性。

### Phase 3：目录级 Codex 导航（完成）

- 为 `.agents/`、`code-as-doc/`、`configs/`、`data/`、`docs/`、`docs/templates/`、`integrations/`、`scripts/`、`tests/`、`tools/` 和 `user-guide/` 增加局部 `AGENTS.md`。
- 保持政策单一来源：局部文件只提供目录地图、局部规则和 targeted validation，冲突时根 `AGENTS.md` 优先。

### Phase 4：文档一致性与验证（进行中）

- 根 `AGENTS.md` 的配置审查入口改为 Codex skill，并明确 Claude 兼容入口。
- 修正用户指南中的旧 `codex/<topic>` 分支示例。
- 把本审计报告加入 `code-as-doc` 和根 README 的维护文档地图。
- 运行 skill frontmatter 校验、文档链接、Ruff、热点守护和完整单测。

## 非目标

- 不创建或猜测未被 Codex 支持的 `.Codex/settings.json`。
- 不启用 Claude hooks，不新增 hook 脚本。
- 不删除或重命名现有 `CLAUDE.md`、`.claude` 或已有 `.agents/skills`。
- 不改 `data/phase2` schema、构建 CLI、依赖版本、生成输出或 review 文件。
- 不在本次任务中继续拆分 Python/JS 热点模块；那属于后续维护 workstream。
