# Code Optimization Log

日期：2026-03-08  
范围：P0 + P1（target 解析去重 / 构建噪声清理 / 模块拆分 / pages schema）

---

## 1. 目标

- 消除 `build_docs / gen_index_bundle / word_bundle` 中重复的 target/token 解析逻辑
- 清理并停止追踪构建产物与缓存文件，降低仓库噪声
- 同步维护规范文档状态

---

## 2. 代码优化内容

### 2.1 抽离 target 公共模块

新增文件：
- `tools/utils/targets.py`

新增共享能力：
- `format_tokenized()`：统一 `{model}` / `{region}` token 渲染与缺参报错（`{sku}` 禁用）
- `config_uses_token_in_pages()` / `config_uses_token()`：统一 token 使用检测
- `resolve_build_model()`：统一 model 入口解析
- `resolve_build_region()`：统一 region 入口解析

### 2.2 构建入口去重改造

已修改：
- `tools/build_docs.py`
- `tools/gen_index_bundle.py`
- `tools/word_bundle.py`

改造结果：
- 3 个入口脚本复用同一套 target 解析能力
- CLI 统一收敛到 `--model/--region`，并禁止 `{sku}` token

---

## 3. 仓库噪声清理

### 3.1 `.gitignore` 更新

已修改：
- `.gitignore`

新增规则：
- `docs/_build/`
- `docs/generated/`
- `**/__pycache__/`
- `*.pyc`
- `.DS_Store`

### 3.2 已追踪噪声文件从 index 移除

执行：
- `git ls-files | rg '^(docs/_build/|docs/generated/)|/__pycache__/|\.DS_Store$'`
- `git rm --cached -r ...`

处理结果：
- 共移除 167 个已追踪噪声文件（仅从 index 移除，不删除本地工作文件）

---

## 4. 规范文档同步

已修改：
- `code-as-doc/code_style_guide.md`

同步内容：
- 新增 “P0 执行状态（2026-03-08）”
- 将路线图中的 P0 标记为“已完成”

---

## 5. 验证结果

### 5.1 语法检查

```bash
python3 -m py_compile tools/build_docs.py tools/gen_index_bundle.py tools/word_bundle.py tools/utils/targets.py
```

结果：通过

### 5.2 单元测试

```bash
python3 -m unittest discover -s tests -v
```

结果：26/26 通过

### 5.3 构建回归

```bash
python3 tools/build_docs.py --model JHP-2000A --region US --clean --no-open
```

结果：
- `docs/generated/JHP-2000A/safety_en.rst` 生成成功
- `docs/generated/JHP-2000A/spec_en.rst` 生成成功
- PDF 生成成功：`docs/_build/latex/manual_demo.pdf`
- DOCX 生成成功：`docs/_build/word/manual_demo_en.docx`

---

## 6. 变更文件清单（本次 P0）

- `.gitignore`
- `tools/utils/targets.py`（新增）
- `tools/build_docs.py`
- `tools/gen_index_bundle.py`
- `tools/word_bundle.py`
- `code-as-doc/code_style_guide.md`
- `code-as-doc/code_optimization_log.md`（新增）

---

## 7. P1 执行记录（2026-03-08）

范围：模块拆分 + `config.pages` dataclass schema

### 7.1 目标

- 拆分 `tools/phase1/renderers.py`，降低单文件复杂度
- 拆分 `tools/word_bundle.py`，分离 context/html/docx 职责
- 为 `config/pages` 引入 typed schema，减少入口脚本裸字典访问

### 7.2 代码改造

新增：
- `tools/config_pages.py`
- `tools/phase1/renderers_common.py`
- `tools/phase1/renderers_safety.py`
- `tools/phase1/renderers_spec.py`
- `tools/phase1/renderers_spec_parser.py`
- `tools/phase1/renderers_symbols.py`
- `tools/word_bundle_common.py`
- `tools/word_bundle_html.py`
- `tools/word_bundle_docx.py`
- `tests/test_config_pages.py`

重构：
- `tools/phase1/renderers.py` 改为薄入口 + renderer 注册
- `tools/word_bundle.py` 改为薄入口 + CLI/兼容导出
- `tools/build_docs.py` 切换 `CsvPage` schema 读取 `config.pages`
- `tools/gen_index_bundle.py` 切换 typed page 对象生成 `index.rst`
- `tools/validate_config.py` 切换 schema 解析校验
- `tools/utils/targets.py` 的 pages token 检测切换 schema 解析

### 7.3 验证

语法检查：

```bash
python3 -m py_compile tools/config_pages.py tools/build_docs.py tools/gen_index_bundle.py tools/validate_config.py tools/utils/targets.py tools/word_bundle.py tools/word_bundle_common.py tools/word_bundle_html.py tools/word_bundle_docx.py tools/phase1/renderers.py tools/phase1/renderers_common.py tools/phase1/renderers_safety.py tools/phase1/renderers_spec.py tools/phase1/renderers_spec_parser.py tools/phase1/renderers_symbols.py
```

结果：通过

单元测试：

```bash
python3 -m unittest discover -s tests -v
```

结果：30/30 通过

构建回归：

```bash
python3 tools/build_docs.py --model JHP-2000A --region US --clean --no-open
```

结果：
- `docs/generated/JHP-2000A/safety_en.rst` 生成成功
- `docs/generated/JHP-2000A/spec_en.rst` 生成成功
- PDF 生成成功：`docs/_build/latex/manual_demo.pdf`
- DOCX 生成成功：`docs/_build/word/manual_demo_en.docx`

---

## 8. 目标解析与产品名关联优化（2026-03-08）

### 8.1 目标

- 移除 `model -> sku` 隐式映射逻辑
- 增加 `region` 目标维度（CLI + config）
- 将 `product_name` 统一改为从 `Spec_Master.csv` 按 `Model + Region + Language` 解析

### 8.2 改动

- 新增：`tools/utils/spec_master.py`
  - `resolve_product_name_from_spec_master()`：按 `Row_key=product_name` 做型号/区域/语言解析
- 修改：
  - `tools/utils/targets.py`：删除 model->sku 自动映射；新增 `resolve_build_region()`；禁用 `{sku}` token
  - `tools/phase1/builder.py`：`BuildSelector` 增加 `regions`；无 SKU 映射时支持 model-only 回退目标；渲染时注入 `product_name`
  - `tools/build_docs.py` / `tools/gen_index_bundle.py` / `tools/word_bundle.py`：
    - 新增 `--region`
    - 统一 region 传递
    - SKU 参数与解析入口移除
  - `tools/word_bundle_common.py` / `tools/word_bundle_html.py` / `tools/word_bundle_docx.py`：
    - 传递 region 上下文
    - bundle 标题与替换变量可用 spec 解析出的 `product_name`
  - `tools/phase1_build.py`：新增 `--region`
  - `tools/validate_config.py`：新增 `build.default_region` 校验
  - `config.yaml`：新增 `build.default_region: US`

### 8.3 测试与回归

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_docs.py --model JHP-2000A --region US --clean --no-open
```

结果：

- 单测 34/34 通过
- phase1/index/latex/pdf/word 构建通过
- `docs/generated/JHP-2000A/spec_en.rst` 继续由同一 `Spec_Master.csv` 源生成，`product_name` 由 model+region+lang 解析

---

## 9. 文档与模板变量同步（2026-03-08）

### 9.1 目标

- 统一 README 与 code-as-doc 文档到当前真实链路
- 明确模板产品名已变量化，且变量值来自 `Spec_Master.csv`

### 9.2 变更

- `README.md`
  - 补充 `|PRODUCT_NAME|` / `|PRODUCT_NAME_BOLD|` 注入流程说明
  - 修正默认路径为 `data/phase1/Spec_Master.csv` 与 `data/phase1/Spec_Footnotes.csv`
- `code-as-doc/spec_master_user_guide.md`
  - 重写为 model+region 主链路说明
  - 明确构建必备字段与 fail-fast 条件（`Row_key=product_name`）
- `code-as-doc/code_style_guide.md`
  - 移除过时 `sku` 维度描述
  - 同步测试门禁命令为 `--model + --region`

### 9.3 结果

- 说明文档与当前代码行为一致
- `spec` 内容源与产品名变量源描述保持单一事实来源（`Spec_Master.csv`）
