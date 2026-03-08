# Code Style Guide (Manual Demo)

本规范用于约束本仓库后续代码演进，目标是让 `rst/html/pdf/word` 构建链路在长期迭代中保持可维护、可扩展、可回归。

适用范围：
- `tools/**/*.py`
- `docs/templates/**/*.rst`
- `data/**/*.csv`
- `config.yaml` 与构建入口脚本

更新时间：2026-03-08

---

## 1. 现状评估（基线）

### 1.1 结构化程度评估

综合评分：**7/10**

优点：
- 主流程清晰：`build_docs -> phase1_build -> gen_index_bundle -> sphinx/latex -> word`
- 配置驱动明显：`config.yaml` 的 `pages` 控制页面顺序与来源
- 有基础数据校验：`validate_config.py`、`validate_layout_params.py`
- 有单元测试基线（26 个用例，覆盖核心路径）

主要问题：
- 模块过大：`tools/phase1/renderers.py`（1000+ 行）、`tools/word_bundle.py`（800+ 行）
- 重复逻辑较多：target 解析、token 处理、model->sku 映射在多个文件重复实现
- 存在跨模块私有方法调用（如 `word_bundle` 调 `builder._load_vars_by_sku()`）
- 构建产物被版本管理追踪（`docs/_build/**`），噪声大且影响可审查性

### 1.2 继承与迭代能力评估

综合评分：**6.5/10**

优点：
- 通过 `PAGE_RENDERERS` + `page_registry.csv` 支持按页扩展
- `BuildSelector` 支持 `sku/model/page/lang` 过滤，利于增量构建
- `spec_master_csv` 已收敛为配置单一来源，方向正确

主要问题：
- 新增页面仍需改动多个点（模板、renderers、config、测试），缺少标准脚手架
- `spec` 的 schema 解析逻辑集中且复杂，修改风险高
- HTML/PDF/Word 虽已趋同，但实现层还未完全共享“统一 target 解析组件”

---

## 2. 架构分层规范（必须遵守）

### 2.1 分层模型

- L0 数据契约层：`config.yaml`、CSV schema、字段校验
- L1 数据装配层：`tools/phase1/builder.py`（读取、过滤、归一）
- L2 渲染层：`tools/phase1/renderers.py`（纯渲染，不做 I/O）
- L3 编排层：`tools/gen_index_bundle.py`（组装 index）
- L4 构建入口层：`tools/build_docs.py`（流程调度）
- L5 导出层：`tools/word_bundle.py`（bundle/docx 导出）

### 2.2 依赖方向

必须满足：`L4 -> L3/L1/L5 -> L2`，禁止反向依赖。

禁止事项：
- 导出层直接调用其他模块的私有方法（`_xxx`）
- 渲染层直接执行 subprocess 或文件写入
- 校验层依赖构建输出目录

---

## 3. 代码组织规范

### 3.1 文件与函数规模

强制标准：
- 单文件建议不超过 **500 行**；超过必须拆分
- 单函数建议不超过 **80 行**；超过 **120 行** 必拆
- 每个文件只承载一个主职责

落地拆分建议（现状改造优先级）：
- `tools/phase1/renderers.py` 拆为：
  - `renderers/safety.py`
  - `renderers/spec.py`
  - `renderers/symbols.py`
  - `renderers/common.py`
- `tools/word_bundle.py` 拆为：
  - target/path 解析
  - rst->html 转换
  - docx 导出与后处理

### 3.2 重用与去重

以下能力必须抽到共享模块（如 `tools/utils/targets.py`）：
- `{sku}/{model}` token 检测与格式化
- `model -> sku` 映射
- default target 解析策略

禁止在 2 个以上脚本重复复制相同解析逻辑。

### 3.3 类型与数据结构

强制标准：
- 跨层传参（尤其 config/page/path）优先 `dataclass`，避免深层 `dict.get(...)`
- 新增公共函数必须写类型注解
- 复杂返回值必须用具名结构（dataclass / TypedDict），禁止“隐式 tuple 协议”

---

## 4. 数据契约与配置规范

### 4.1 CSV 契约

强制标准：
- 每个 CSV 必须有“最小必需字段”定义
- 校验失败必须包含：文件名 + 行号 + 字段名
- 禁止 silent skip（除非明确记录为可选字段）

### 4.2 config 规范

强制标准：
- 主链路默认以 `build.default_model` 驱动
- 新功能必须通过 config 控制，禁止硬编码路径
- token 仅允许 `{model}` / `{sku}`，新增 token 必须先补校验器

### 4.3 单一事实源（Single Source of Truth）

强制标准：
- `spec` 页面仅使用 `paths.spec_master_csv`（主源）+ `paths.spec_footnotes_csv`（可选补充）
- `html/pdf/word(bundle)` 必须共享同一 `csv_page -> generated rst` 内容源

---

## 5. 渲染与构建规范

### 5.1 渲染层

强制标准：
- 统一 escape 入口（RST/LaTeX/HTML）
- 模板占位符替换必须可预测，不得注入动态副作用
- 对 `raw:: latex/html` 使用白名单模式，不允许 CSV 直接透传原始命令

### 5.2 构建可复现性

强制标准：
- 遍历顺序必须显式排序（glob/list/dict）
- 同输入应产出可复现输出
- 禁止将构建产物提交到版本库

必须调整 `.gitignore`（P0）：
- `docs/_build/`
- `docs/generated/*`（若需要保留样例，放单独 fixtures 目录）
- `**/__pycache__/`
- `.DS_Store`

---

## 6. 测试规范

### 6.1 测试门禁（合并前必须通过）

```bash
python3 tools/validate_config.py --config config.yaml
python3 tools/validate_layout_params.py --csv data/layout_params.csv
python3 -m unittest discover -s tests -v
python3 tools/build_docs.py --model JHP-2000A --clean --no-open
```

### 6.2 测试分层

必须覆盖：
- 单元测试：解析函数、过滤逻辑、escape、target 解析
- 契约测试：CSV 缺字段/错字段/多语言缺失行为
- 集成测试：最小链路（phase1 -> index -> latex）

新增/修改页面时，至少新增：
- 1 个正常路径测试
- 1 个 schema 错误测试
- 1 个过滤条件测试（model/region/project_code/enable）

---

## 7. 错误处理与日志规范

### 7.1 错误处理

强制标准：
- Fail Fast，禁止吞错
- 错误信息必须可定位数据源
- CLI 失败必须返回非 0

推荐错误格式：
`[module] <file> line <n>: <field> <reason>`

### 7.2 日志

强制标准：
- 关键阶段必须打日志：validate / render / build / export
- 日志前缀统一（如 `[build]`、`[phase1_build]`）

---

## 8. 变更流程规范（PR/Review）

每个 PR 必须包含：
- 改动动机（问题/目标）
- 影响范围（数据契约/渲染/构建/导出）
- 回归命令与结果
- 若改 CSV schema，必须更新文档（README 或专门 guide）

Review 必查项：
- 是否新增重复逻辑（target/token/selector）
- 是否引入跨层耦合
- 是否破坏 html/pdf/word 同源性

---

## 9. Do / Don't（硬性清单）

Do：
- 用配置驱动行为，不写死路径
- 把复杂逻辑拆成可测试纯函数
- 所有新增字段先加校验再加业务逻辑

Don't：
- 不要在多个入口脚本复制同一解析逻辑
- 不要从一个模块调用另一个模块的私有函数
- 不要把 `_build` 产物提交到仓库
- 不要在渲染函数里混入 I/O 或 subprocess

---

## 10. 分阶段改造路线（建议）

P0（立即）：
- 抽离 `target` 解析共享模块，消除 `build_docs/gen_index_bundle/word_bundle` 重复逻辑
- 清理并禁止跟踪构建产物（`.gitignore` 与仓库清理）

P1（短期）：
- 拆分 `renderers.py`、`word_bundle.py`
- 为 `config/pages` 引入 dataclass schema，减少裸字典访问

P2（中期）：
- 增加 CI（至少跑 validate + unittest + model 构建 smoke）
- 引入快照测试（generated rst 与关键模板片段）

---

## 11. Definition of Done（完成定义）

任意功能改动满足以下条件才可视为完成：
- 代码符合本规范（分层、去重、类型、错误处理）
- 测试与构建门禁全部通过
- 文档与契约同步更新
- 不引入新的构建噪声文件

