# IDML 样式契约欠账清算 — 实施计划

Discovery：[`../reviews/idml_style_contract_debt_discovery_2026-08-05.md`](../reviews/idml_style_contract_debt_discovery_2026-08-05.md)。

## Phase A — 等价批准装配路由

目标：已批准 target 在 `build.py idml --source auto` 下使用冻结 `review-asis`；显式 source 选择保持不变，未批准 target 继续 runtime。

文件：

- `tools/build_dispatch.py`
- `tests/test_build_dispatch.py`
- `code-as-doc/build_doc_guide.md`
- `user-guide/hello_auto-doc.md`
- `user-guide/quick_start_guide.md`

验收：dispatch characterization tests；真实 `build.py idml --source auto --idml-mode flow` 生成与显式 `review-asis` 相同的 52 个 source refs。

## Phase B — Warranty 显式语义

目标：共享 Latin/manual-family Warranty 模板通过 container class 显式声明 lead、section、years，IDML 不再依赖标题或年限措辞来决定组件角色。

文件：

- `docs/templates/page_shared/*/11_warranty.rst`
- `tools/idml_rst_extract.py`
- `tools/idml/oppanel.py`
- `tests/test_idml_rst_extract.py`
- `tests/test_idml_oppanel.py`

验收：改变 section 标题和 years 文案仍保留组件类型；未标记 frozen review 保持兼容；EN/FR/ES runtime bundle 均产生明确组件。

## Phase C — 11 条样式债残余

目标：把当前仍存在的 renderer-local visible constants/策略接入 token 或明确 IDML 合同；已在后续代码修好的陈旧债用 characterization test 证明后销账。

文件：

- `tools/idml/styles.py`
- `tools/idml/prose_paragraph.py`
- `tools/idml/components/prose_table.py`
- `tools/idml/spec_tables.py`
- `tools/idml/components/notice.py`
- `tools/idml/components/callout.py`
- `tools/idml/symbols_page.py`
- `data/layout_params.csv`
- 对应 `tests/test_idml_*.py`

验收：每个债至少一个直接 contract assertion；所有新 token 都有消费方；`manual_style.yaml` 的对应条目改为 `aligned` 且 `debt: []`。

## Phase D — 参数生成与重新批准

顺序：

1. `python3 tools/csv_to_tex_params.py`；
2. 最终 `review-asis` flow 构建，确认 52 source refs / 58 physical composition map 不变；
3. 用 `reference_layout_scaffold.py` 从现有批准 plan 生成完整候选；
4. 对照 source refs、languages、composition map、skipped_raw 与全部 identity；
5. 按 2026-08-05 操作者批准更新 approval metadata 并激活同一路径合同；
6. `check_reference_layout_pins.py` 与 production IDML fail-closed 验证。

## Phase E — 完整关闭

验证梯度：

```bash
python3 -m ruff check build.py integrations tools tests scripts
python3 -m unittest <targeted modules>
python3 -m unittest
python3 tools/check_maintainability_guardrails.py
python3 tools/check_reference_layout_pins.py
python3 tools/check_doc_link_integrity.py
python3 build.py idml --config configs/config.us.yaml --model JE-1000F --region US --source auto --idml-mode both --no-clean
```

完成后更新 `code-as-doc/dev/style_debt_execution_status.md`，明确已销、归口、非代码资产债和实际验证结果。
