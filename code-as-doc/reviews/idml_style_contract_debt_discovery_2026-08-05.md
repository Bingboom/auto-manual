# IDML 样式契约欠账清算 discovery（2026-08-05）

## 结论

`fix/idml-style-contract-debt` 可以继续，但必须拆成四个独立验证阶段。批准版式并未缺页：`docs/_review/JE-1000F/US/index.rst` 可生成 52 个 Manual-IR 源页绑定，对应批准合同的 58 个物理页。真正的装配缺口是 `tools/build_dispatch.py::_dispatch_idml_action` 在 `--source auto` 下把所有 IDML 目标都强制为 `runtime`，没有让已批准目标使用冻结 review derivative。

操作者在 2026-08-05 明确批准：

1. 建立与冻结 `review-asis` 等价的 production IDML 批准装配路由；
2. 对当前内容重新批准并重绑 reference-layout content hash；
3. 给共享 Warranty 模板增加语义标记；
4. 完成剩余实现并更新 `manual_style.yaml` 正式销账。

## 当前可复现基线

- 分支基点：`789ae3e44a1edf13491eba32f85355d3363d25cd`。
- 独立 worktree：`/private/tmp/auto-manual2-idml-style-contract-debt.wNNtaQ`。
- 已有未提交工作：Auto Resume 显式角色、Warranty 降级 warning、对应测试和执行状态文档，共 6 个文件。
- 真实入口：

  ```bash
  python3 build.py idml \
    --config configs/config.us.yaml \
    --model JE-1000F \
    --region US \
    --source review-asis \
    --idml-mode flow \
    --no-clean
  ```

- 基线输出：`pages=52`、`blocks=570`、`skipped_raw=0`。
- 52 个 `source_ref` 与批准 plan 顺序逐项相同；批准 plan 的 52 个绑定覆盖 58 个物理页。
- 当前 Manual-IR content hash `ced5ae20…`，批准值 `031e4d2f…`；这是当前 rebind 的首要拒绝条件。

## Load-bearing 入口与合同

| 责任 | 入口 | 当前事实 |
|---|---|---|
| IDML 装配路由 | `tools/build_dispatch.py::_dispatch_idml_action` | 显式 `review` / `review-asis` / `runtime` 会保留；`auto` 一律变成 `runtime` |
| 冻结 review 装配 | `tools/build_docs_bundle.py` | `review-asis` 只物化 conf/asset skeleton，再覆盖完整 review 内容 |
| 批准合同 | `docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json` | 52 源绑定、58 物理页、批准状态有效 |
| 普通 rebind | `tools/idml/reference_layout_rebind.py` | 只允许非内容 identity 与逐页 source hash 变化；content 变化必须重新 review/approval |
| 新内容 review | `tools/reference_layout_scaffold.py` | 保留 composition map，刷新全部 identity/page hash，输出非激活 draft |
| 样式 pin | `tools/check_reference_layout_pins.py` | 严格校验 tracked 的 style/layout hash，不自动批准 |
| Warranty 识别 | `tools/idml_rst_extract.py` + `tools/idml/oppanel.py` | extractor 尚不识别 `container::`；当前靠 h1/h2/年限文本形状组合 |

## 11 条 pin 债的实际残余

审计以当前代码为准，而不是照抄 PR #874 的旧清单：

| 债 | 当前残余 | 预计修改面 |
|---|---|---|
| `HB-TITLE-L1` | `comp_h1_pill_height` 已在 IDML 使用；欠账记录已陈旧 | characterization test + 正式销账 |
| `HB-TITLE-L2/L3` | 段落样式没有 IDML keep-with-next | `tools/idml/styles.py` + tests |
| `HB-TYPE-LIST` | 普通列表只用 `idml_list_font_leading`，没有 FR/ES 类型化级联 | `styles.py`、`prose_paragraph.py` + tests |
| `HB-TABLE-TROUBLESHOOTING` | 12 行 minima、single-height 修正、内/外线、panel floor/import allowance 仍是本地常量 | `prose_table.py`、`data/layout_params.csv` + tests |
| `HB-TABLE-SPEC` | 固定 `SingleRowHeight=10.3`，多行最低高度没有显式 token 合同 | `spec_tables.py`、layout params + tests |
| `HB-CALLOUT-STRIP` | 生产 notice 大部已 token 化；列表悬挂缩进仍硬编码 3.4pt | `components/notice.py` + tests |
| `HB-SAFETY-WARNING` | icon 列、icon 上限、panel 最低高度仍是 24/18/28pt 常量 | `components/callout.py`、layout params + tests |
| `HB-TABLE-SYMBOL-SIGNAL/ICON` | 表行/列核心已 token 化；组合器仍有 subbar、段间 gap、H1 光学偏移、底部 allowance 常量 | `symbols_page.py`、layout params + tests |

## Warranty 语义标记设计

共享 RST 使用显式 container class，保留 LaTeX/Sphinx 可读性：

```rst
.. container:: warranty-lead

   **Localized lead copy.**

.. container:: warranty-section warranty-years

   Warranty Period
   ---------------

   .. list-table::
      ...
```

普通 section 使用 `warranty-section`，年限 section 额外带 `warranty-years`。IDML extractor 将这些 class 解析为显式 semantic-container block；`oppanel` 只在标记范围内生成 `warrantylead`、`warrantysection`、`warrantyyears`。未标记 review derivative 暂保留兼容识别和 warning，防止已冻结 review 立即失效。

影响面是 `docs/templates/page_shared/*/11_warranty.rst`。JP、ZH 是独立模板线，本轮不改，避免把 Latin/shared 语义结构强加给不同的 warranty 版式。

## 风险与安全网

- 不改批准 composition map、reference PDF identity、物理页起止或页数。
- content 重新批准必须从最终 Manual IR scaffold，不能手改局部 page hash。
- `data/layout_params.csv` 每次改动后运行 `python3 tools/csv_to_tex_params.py`，并审计生成副作用。
- 共享 Warranty 模板先以 extractor tests 锁住 EN/FR/ES，再跑真实 `review-asis` 与 runtime/template 构建。
- 每阶段依次运行 Ruff、定向 unittest、全量 unittest、guardrails、pin、docs link，最后真实 IDML。
- `_build`、`docs/index.rst`、reports 生成副作用完成后精确 restore/clean；不删除 review 源或 phase2 附件。

## 非目标

- 不合入或修补 #885；共享 manifest 不是 8/1 批准装配来源。
- 不处理 10 条“归口不单修”长期项。
- 不改变 reference PDF、composition map 或页面视觉目标。
- 不提交、推送、创建 PR 或合并；这些 GitHub 动作分别等待明确授权。
