# 样式契约欠账清算 — 执行状态

集成分支 `fix/idml-style-contract-debt`（基于 `origin/main` @ `aff00e32`）。计划见欠账清单（PR #874 分支上的 `docs/renderers/contracts/STYLE_DEBT.md`）：26 条债，其中 16 条排期修，10 条归口。

**16 条里已销 1 条。** 剩 15 条中 11 条被参考版式 pin 硬阻塞，4 条可继续。

---

## 1. 已完成

| # | 内容 | 提交 / PR | 销债 |
|---|---|---|---|
| 1 | `danger` 保留自己的 notice variant | [#884](https://github.com/Bingboom/auto-manual/pull/884) → `c25fef27` | `HB-SAFETY-DANGER` |
| — | phase2 sync 坐标落盘 | `ded45827` | 无（基础设施） |

`HB-SAFETY-DANGER` 的剩余债已收窄为**缺 DANGER lockup 美术资产**——LaTeX `HBDangerBlock` 同样拿 warning lockup 顶着（`components_safety.tex:171` 注释写明），三处渲染行为一致，要走 asset intake，不是代码问题。

## 2. 待确认（已开 PR，未合）

| PR | 内容 | 卡在哪 |
|---|---|---|
| [#885](https://github.com/Bingboom/auto-manual/pull/885) | manifest 补回目录页与封底 | 需要操作者提供 8/1 那次的 bundle 装配方式 |

`docs/manifests/manual_us.yaml`（以及其余 16 个 manifest）都不含 `00_toc.rst` / `99_back_cover.rst`，所以每次 US 构建都装出 50 页——**没有目录页、没有封底**。已批准参考版式钉的是 52 页。加回两页后页数对上（52/571 blocks），全量 unittest 绿，但 pin 的两个条件在当前 ordinal 规则下互斥：

| toc 位置 | 页数 | `pNN_` 前缀 | IR 里 toc 位置 |
|---|---|---|---|
| `00_preface` 之后 | 52 ✓ | p21（pin 要 p20）✗ | index 2 ✓ |
| manifest 末尾（#885 当前形态） | 52 ✓ | p20 ✓ | index 50（pin 要 2）✗ |

根因：`tools/gen_index_bundle_plan.py:125` 的 `enumerate(pages, start=1)`，`pNN_` 前缀取 manifest 条目序号，toc 一占号后面重名页前缀全体 +1。

## 3. 硬阻塞：11 条

`tools/check_reference_layout_pins.py` 校验两个 pin，任一漂移即红：

| pin | 来源 | 谁会碰 |
|---|---|---|
| `style_contract_sha256` | `docs/renderers/contracts/manual_style.yaml` | **每条债的销账**（改 `debt` / `status` 字段） |
| `layout_params_sha256` | `data/layout_params.csv` | **P1/P2 的 token 化**（核心动作就是加 token） |

重绑只有 `tools/reference_layout_rebind.py --manual-ir <manual.ir.json> --write` 一条路，而它**拒绝改变页面集合**（只刷 sha）。所以 §2 那个门不修好，这 11 条动不了：

- P1：`HB-TITLE-L2`、`HB-TITLE-L3`（keep-with-next）、`HB-TYPE-LIST`（语言密度级联）、`HB-TABLE-TROUBLESHOOTING`（六项校准常量 + yaml 逗号碎片合一）、`HB-TABLE-SPEC`（行高 token 化 + 三渲染器列宽哨兵）
- P2：`HB-TITLE-L1`（band 高度）、`HB-CALLOUT-STRIP`（变体几何）、`HB-SAFETY-WARNING`（本地常量）、`HB-TABLE-SYMBOL-SIGNAL` + `-ICON`（页面合成器常量）

## 4. 可继续：4 条

不碰 `manual_style.yaml` 与 `data/layout_params.csv`，pin 门保持绿。销账动作留到门修好后统一补。

| 债 | 现场 | 做法 |
|---|---|---|
| `HB-WARRANTY-LEAD` / `-SECTION` / `-YEARS` | `tools/idml/oppanel.py::_group_warranty_page`（门是「有 h1 + 有 h2 + 有 warrantyyears 组件」，否则 `return blocks` **静默放弃**）；`_parse_warranty_cell` 靠正则认「数字+单位+标签+文本」 | 彻底改成读语义类型需要在共享模板加 `.. container::` 标记（`11_warranty.rst` 里目前只有 `list-table` 和 `only:: region_*`），影响所有型号 + LaTeX 侧，需操作者拍板。**可先做的半步**：把静默放弃改成可观测（warning + 落 trace），并加测试锁住当前识别 |
| `HB-TABLE-AUTO-RESUME` | `tools/idml/components/` 无 auto_resume 角色，落到通用 data_table | 加显式角色，对齐 `table_auto_resume` IR kind，目标 golden 字节不变 |

## 5. 归口不单修：10 条

- 挂起 4 条，等对应版式真要动时顺势做：`HB-TABLE-LCD-MODE`、`HB-SPECIAL-FCC`、`HB-SPECIAL-INBOX`、`HB-SPECIAL-OVERVIEW`
- 并入立项 6 条：样式借用三条（`HB-TYPE-LEAD` / `-FOOTER` / `-PAGE-NUMBER`）等动 `type_system` 时一并；页计划三条（`HB-PAGE-*`）归共享页计划立项

## 6. 待操作者决策的三件事

1. **8/1 那次含目录页和封底的 bundle 怎么装的？** 决定 #885 怎么收（改 ordinal 语义 / scaffold 新 plan / 照原样复原）。不解决则 production IDML 构建一直红，11 条债一直冻。
2. **质保三条要不要在共享模板加语义标记？** 决定第 4 节那三条是彻底修还是只加护栏。
3. **`sync-data` 的 0 行覆盖要不要加护栏？** 见第 8 节。

## 7. 环境要点（复现用）

- 权威数据：`set -a && . scripts/phase2_sync.env.example && set +a`，再 `python build.py sync-data --config configs/config.us.yaml`。认证走 lark-cli 已登录 profile（本机 profile 名是 appId，不是 `prod`）。
- **产出 manual IR 不必过 same-source 门**：`build.py idml --idml-mode flow` 会写 `docs/_build/<MODEL>/<REGION>/idml/flow/manual.ir.json`（production 路径下 IR 落盘在门之后，门失败就拿不到文件）。rebind 就用这个文件。
- **IDML 构建会改动/删除 tracked 的 `docs/_build/**` 与 `docs/index.rst`**。跑完必须 `git checkout -- docs/_build docs/index.rst reports/`，否则脏改动会被夹带进提交。加 `--no-clean` 可少删一批。

## 8. 顺带发现的两个缺陷（未修）

- **`sync-data` 会把非空镜像覆盖成 0 行**。实测把 `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID` 指到 `02_主数据_产品信息表`（只有一个「是否支持加电包」字段）时，输出 `model_capabilities: rows=0 changed=yes`，`data/model_capabilities.csv` 被写成只剩表头。能力门的数据源一旦被清空，下一次构建会把所有带 `capability:` 条件的小节全裁掉，而且不报错。建议：拒绝把非空镜像覆盖成 0 行。正确坐标是 `02_主数据_Document_key`（`tbltnkDIdwiDOP7d` / `vewi97AFwi`），九个 checkbox 对应 CSV 九列。
- **`tools/idml/flow_idml.py:617` 的 `_fence_style()` 全仓库无调用者**，是死代码，里面还有第二处 `danger → warning` 别名。

## 9. 已核实、不构成问题的三件事

调查过程中我曾误判，这里记下结论以免重复：

- **能力门裁掉 `07_extra_battery.rst` 是正确的。** manifest 里三条都带 `capability: 加电包扩容`，JE-1000F 该项为 FALSE，产品本身不支持加电包，手册从未有这一页。pin 里也没有它。
- **`加电包扩容` / `并机/扩展` 两列全型号 FALSE 是权威事实，不是镜像漂移。** sync 下来的 `model_capabilities.csv` 与仓库那份 sha 完全一致（`cdf29b10…`，30 行）。
- **参考版式 pin 不是过期。** `approval` 字段：`approved_by: 唐夏冰`、`approved_at: 2026-07-31`、`method: 按现网内容重批契约; includes the merge-splice guard and p26 grid repair`——即 8/1 那次 1.7 publish 的基线。问题在 manifest 缺页，不在 pin 陈旧。
