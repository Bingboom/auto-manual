# 代码文档化规范（Documentation Maintenance）

更新时间：2026-03-08

本规范用于明确：每次代码结构优化、功能修改或新增代码时，必须同步维护哪些文档，保证仓库长期可读、可维护、结构清晰。

---

## 1. 适用范围

- `tools/**/*.py`
- `docs/templates/**/*.rst`
- `data/**/*.csv`
- `config.yaml`
- 测试与构建脚本

---

## 2. 文档职责（Single Source of Truth）

- `README.md`
  - 面向使用者的真实构建逻辑、命令入口、配置项说明、链路说明。
- `code-as-doc/code_style_guide.md`
  - 面向开发者的架构分层、编码规范、测试门禁、重构路线。
- `code-as-doc/code_optimization_log.md`
  - 每次结构优化/重构的变更记录、影响范围、验证结果。
- `code-as-doc/spec_master_user_guide.md`
  - `Spec_Master.csv` 在构建链路中的作用、字段定义、Word 构建必需字段。
- `code-as-doc/tests/README.md`（如存在测试策略变化）
  - 测试组织方式、执行命令、覆盖边界。

---

## 3. 变更类型 -> 必维护文档

## 3.1 代码结构优化/重构（模块拆分、公共逻辑抽离、依赖方向调整）

必须更新：
- `code-as-doc/code_optimization_log.md`：记录目标、改动文件、回归结果。
- `code-as-doc/code_style_guide.md`：若规范/分层约束发生变化，必须同步。
- `README.md`：若入口命令、构建流程、配置语义变化，必须同步。

至少补充：
- 对应测试或回归命令结果（单测/构建 smoke）。

## 3.2 新增功能（新页面类型、新渲染器、新 CLI 参数、新导出路径）

必须更新：
- `README.md`：功能用途、配置方式、执行命令、限制条件。
- `code-as-doc/code_style_guide.md`：若引入新的层级边界或开发约束，必须同步。

条件更新：
- 若涉及 `Spec_Master.csv` 读取逻辑或字段语义：同步更新 `code-as-doc/spec_master_user_guide.md`。
- 若测试策略变化：同步更新 `code-as-doc/tests/README.md`。

## 3.3 配置变更（`config.yaml` 字段新增/删除/重命名）

必须更新：
- `README.md`：配置字段说明、默认值、优先级、迁移方式。
- `code-as-doc/code_optimization_log.md`：记录兼容性影响和回归结论。

## 3.4 数据契约变更（CSV 字段、过滤条件、必填规则）

必须更新：
- `code-as-doc/spec_master_user_guide.md`：字段定义、必填项、筛选逻辑、示例。
- `README.md`：如果构建链路的输入源、路径或行为变化，必须同步。
- `code-as-doc/code_optimization_log.md`：记录契约变更影响范围与验证结果。

## 3.5 构建链路变更（html/pdf/word 任一流程）

必须更新：
- `README.md`：构建顺序、工具依赖、命令示例。
- `code-as-doc/code_optimization_log.md`：记录为何改、改了什么、如何验证。

强制要求：
- 明确说明是否仍保持 `html/pdf/word` 同源（同一 CSV + RST 内容源）。

## 3.6 纯内容改动（RST 文案、版式、不改代码逻辑）

必须更新：
- 相关 RST 页面文件本身。

条件更新：
- 如果目录层级或标题级别策略变化，需更新 `README.md` 对应说明。

---

## 4. 文档维护最小规则（强制）

- 规则 1：任何“用户可见行为”变化，必须更新 `README.md`。
- 规则 2：任何“架构/分层/共享逻辑”变化，必须更新 `code-as-doc/code_style_guide.md` 或 `code-as-doc/code_optimization_log.md`。
- 规则 3：任何“CSV 字段/过滤条件”变化，必须更新对应数据指南（`code-as-doc/spec_master_user_guide.md`）。
- 规则 4：文档更新与代码改动必须同 PR/同提交链路完成，禁止后补。

---

## 5. 提交前检查清单（可直接执行）

- [ ] 代码改动与文档改动已一一对应。
- [ ] `README.md` 中命令和配置示例可执行。
- [ ] 若改动构建链路，已记录在 `code-as-doc/code_optimization_log.md`。
- [ ] 若改动规范/架构边界，已更新 `code-as-doc/code_style_guide.md`。
- [ ] 若改动 `Spec_Master.csv` 契约，已更新 `code-as-doc/spec_master_user_guide.md`。
- [ ] 单测与构建 smoke 至少执行一次并记录结果。

推荐回归命令：

```bash
python3 tools/validate_config.py --config config.yaml
python3 tools/validate_layout_params.py --csv data/layout_params.csv
python3 -m unittest discover -s tests -v
python3 tools/build_docs.py --model JHP-2000A --clean --no-open
```

---

## 6. 评审口径（Review Checklist）

- 是否新增了重复逻辑而未抽象复用。
- 是否出现跨层调用私有函数或职责混杂。
- 是否更新了对应文档且内容与当前代码一致。
- 是否破坏 `html/pdf/word` 同源构建原则。

---

## 7. 执行策略（建议）

- 小改动：最少更新 `README.md` 或相关专题文档，并补回归结果。
- 中改动：同步更新 `README.md + code-as-doc/code_optimization_log.md`。
- 大改动（重构）：同步更新 `README.md + code-as-doc/code_style_guide.md + code-as-doc/code_optimization_log.md`，必要时补专题指南。

