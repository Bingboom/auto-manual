# 继承与覆盖机制贯彻度评估 — auto-manual

> 参照模型：esp-docs「继承与覆盖」核心概念（六层金字塔 + 复用/灵活/低维护/自动化/可扩展）。
> 方法：把金字塔逐层对到仓库实际代码，结论均带 `file:line` 证据。日期 2026-05-30。
>
> 说明：本文件内所有文件引用使用反引号代码片段（非 Markdown 链接），以兼容 `tools/check_doc_link_integrity.py`
> （该检查器相对文档自身目录解析链接、且不剥离 `:line` 后缀）。

## 背景与纠偏

本仓库不是 esp-docs 那种 HTML-first 站点——所有配置 `build_html: false`，主产物是 PDF（XeLaTeX）与 Word。
因此「没有自定义 Furo 主题、没有 Jinja `{% block %}` 继承」**基本不构成缺陷**；仓库真正的「模板主题层」是 LaTeX renderer 栈，评判落在那里。

## 一、总体三问

- **代码冗余**：整体低（逻辑「写一次+参数化」）；冗余集中在多语言合并配置裸抄。
- **可维护性**：良好（`tools/utils/path_utils.py` 单一事实源 + `tools/check_maintainability_guardrails.py` 行数闸 + 71 个测试文件 + `build.py` 749 行薄分发）。
- **贯彻度**：骨架层强（甚至超纲），内容层与表现层不彻底。

## 二、分层评分

| 金字塔层 | 仓库对应物 | 贯彻度 | 说明 |
|---|---|:---:|---|
| ① 公共配置层 | `configs/config-bases/*.yaml` + `docs/conf_base.py` | 🟡 中 | 机制满分；合并族配置 us/eu/ja 无共同 base |
| ② 语言/覆盖层 | `config.us-en.yaml` 等 + `docs/conf.py` | 🟢 强 | 单语言只写 delta；`docs/conf.py:11` 教科书级 `import *`+override |
| ③ 构建脚本层 | `build.py` + `path_utils` + 目标循环 | 🟢 强 | 单一参数化循环、路径单一事实源 |
| ④ 模板主题层 | LaTeX renderer 栈 / `docs/templates` | 🟡 中 | LaTeX 有组合+覆盖默认值；RST 用路径回退选择（对 PDF 管线可接受） |
| ⑤ 样式资源层 | `hb_manual.css` / `params.tex` / review overrides | 🟡 中 | `params.tex` 数据驱动好；CSS 单体、override 整文件覆盖（HTML 已禁用，低风险） |

## 三、贯彻得好的地方（证据）

1. Sphinx 配置教科书级 `import *`+override：`docs/conf.py:11` `from conf_base import *` 后只覆盖 `master_doc`/`latex_documents`；`docs/conf_base.py` 留 `append_preamble()` 钩子注「子类可覆盖」。
2. 配置加载器是 `import *` 的升级版：`tools/config_loader.py:33-62` 递归 `extends` 合并 + 深拷贝 + 循环检测 + 相对路径解析。
3. 单语言变体只写 delta：`configs/config.us-en.yaml`/`configs/config.eu-fr.yaml` 仅 9–13 行。
4. 路径单一事实源：`tools/utils/path_utils.py` = `PathSegments` 常量 + `Paths` 类 + `*_of(base)` 注入式助手。
5. 单一参数化构建循环：解析集中在 `tools/utils/targets.py` + `tools/build_docs_targets.py`，循环只在 `tools/build_docs_entry.py:76-97` 写一次，各命令复用、无逐变体复制。
6. LaTeX 层确实在覆盖：`docs/conf_base.py:85-100` 用 `\ifdef{\sphinxmaketitle}{\renewcommand...}{}` 覆盖 Sphinx 默认宏；`params.tex` 由 `data/layout_params.csv` 数据驱动生成。

## 四、冗余与问题（证据）

### P1 配置重复
`sync.phase2` 块在 4 处逐字相同：`configs/config.us.yaml:46-89`、`configs/config.eu.yaml:42-85`、`configs/config.ja.yaml:33-75`、`configs/config-bases/eu-single-language-base.yaml:23-65`。
`paths` 块 us/eu/ja 仅 `page_manifest` 不同（其余 9 键全同）；约 12 个 build flags 相同。
us/eu/ja 当前**无 `extends`**，可安全抽 base；`configs/config.zh.yaml` 孤儿（paths 集更精简，需单独处理）。

### P2 硬编码路径（绕过 path_utils，均为 CLI 默认值/非核心工具，值为相对路径）
`tools/content_assembly.py:30`（`FORBIDDEN_OUTPUT_DIRS`）、`tools/readthedocs_source.py:29`（`--build-root` 默认）、`tools/diff_report.py:75`（`--tracked-root` 默认）、`tools/process_docs/build_review_preview.py:250` 与 `:272`（`f"docs/_review/..."`）、`tools/crop_warning_lockup.py:15-16`（资产路径）。影响低：核心 build-path 逻辑干净，集中度约 85–90%。

### P3 表现层（收益存疑，HTML 已禁用）
`docs/_static/hb_manual.css`（697 行）+ `hb_paged.css`（1793 行）单体；review override（`tools/review_support.py:229-261`）是 `shutil.copy2` 整文件覆盖，非 delta 合并。仅在强化 HTML/override 复用时才值得动。

## 五、可维护性信号（正面）

行数闸 `tools/check_maintainability_guardrails.py`（8 个热点全未超）；`tests/` 71 文件约 2.7 万行；`build.py` 749 行薄分发；AGENTS.md §3 明令禁止并行路径模块、代码仅一套 `PathSegments`/`Paths`/`build_paths`。

## 六、建议（分级）

| 级别 | 内容 | 风险 | 收益 |
|---|---|---|---|
| P1 | 抽 `configs/config-bases/phase2-sync-base.yaml`，us/eu/ja `extends` | 低 | 去 ~88 行重复、补继承链 |
| P2 | 5 处硬编码 → `PathSegments` 组合（值不变） | 低 | 集中度 →95%+ |
| P3 | zh 配置归位 + CSS delta 化 + override 改 delta 合并 | 中高、需拆 PR | 收益存疑（HTML 禁用），按需 |

## 七、一句话总结

机制/骨架层是「继承与覆盖」的优等生，部分（递归 extends、路径单一事实源、参数化构建循环）超出笔记描述；真正欠的是把多语言合并配置接进继承链（P1）与若干硬编码路径收口（P2）。表现层与 esp-docs 的 HTML 范式差异属**合理偏离**而非缺陷。
