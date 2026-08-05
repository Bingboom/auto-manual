# 参考版式重绑 + finalize + parity Runbook（JE-1000F US）

Registered: 2026-07-27

## 0. 为什么有这份文件

批准 reference-layout plan v2 把身份拆成 `content`、`assembly`、`style` 和
`provenance`。目标内容、语义/物理装配、样式与逐页 digest 是 production 硬门禁；
全局 phase2 `snapshot_sha256` 只记录在 provenance，不再因为无关表刷新阻断一个
内容完全相同的目标。因此，**只发生 snapshot 漂移时不需要重绑**。

这份 runbook 现在用于两类需要证据的操作：style/layout/page digest 确实变化但
批准内容和装配不变时的原子重绑，以及之后的 InDesign finalize + parity。若
content 或 assembly identity 变化，普通重绑会拒绝，必须回到操作者批准路径。

同时它补上另一笔欠账：#720 把
`lang_en_idml_ups_caution_space_after` 从 9.9pt 改成 15.9pt，
[#724](https://github.com/Bingboom/auto-manual/pull/724) 让契约重新描述了实际
提交的文件，但**这个几何从未经 parity 验证**。第 6 步就是补这个证据。

相关：[`indesign_second_host_runbook.md`](indesign_second_host_runbook.md)
是"换一台 Mac 也能跑 finalize"的主机验证流程，产物**故意写临时目录**；本文
相反，产物必须落进仓库构建目录才会被发布记录采集。

前置：一台装了 **Adobe InDesign 2026** 的设计 Mac；仓库在 `main`（≥ `b91cb393`）。

## 1. 参考 PDF（唯一需要人工提供的输入）

参考 PDF 不在仓库里，必须由操作者提供并核对：

| 项 | 值 |
| --- | --- |
| 文件名 | `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf` |
| SHA-256 | `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2` |
| 字节数 | `5273218` |
| 页数 | 58 |

```bash
shasum -a 256 ~/ref/"Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf"
```

哈希对不上就停——后续每一步都以它为基准。

## 2. 同步一份新的 phase2 快照

这一步提供本次构建的实际源数据。其全局 hash 会进入 provenance，但只有当前
target 实际投影出的内容和逐页 digest 参与批准激活。

```bash
python build.py sync-data --config configs/config.us.yaml --data-root data/phase2
```

## 3. 产出 manual.ir.json

普通 production 可以直接运行；仅在需要预先检查或重绑 style/provenance/page
digest 时，可先用 flow 模式独立产出 IR：

```bash
python build.py idml --config configs/config.us.yaml --model JE-1000F --region US \
  --source review-asis --data-root data/phase2 --idml-mode flow
```

产物：`docs/_build/JE-1000F/US/idml/flow/manual.ir.json`

## 4. 重绑：先 dry-run，看清它要改什么

```bash
python tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir docs/_build/JE-1000F/US/idml/flow/manual.ir.json
```

**放行条件**：

```
identity=<none-or-style/provenance fields>  page_bindings=0  composition_map=unchanged  validation=passed
```

`page_bindings=0` 与 `composition_map=unchanged` 是安全闸。普通 dry-run 还必须
不包含 `content.manual_content_sha256` 或 `assembly.sha256`；若出现，**停下**，
那意味着批准内容或装配真的变化，应走显式批准而不是普通重绑。仅
`provenance.snapshot_sha256` 变化不影响 production，也不要求为了追平而写契约。

确认后写入：

```bash
python tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
  --manual-ir docs/_build/JE-1000F/US/idml/flow/manual.ir.json --write
```

## 5. 生产 IDML

```bash
python build.py idml --config configs/config.us.yaml --model JE-1000F --region US \
  --source review-asis --data-root data/phase2 --idml-mode production
```

预期 `[export-idml] … spreads=60`，产物落在 `docs/_build/JE-1000F/US/idml/`。

## 6. finalize（设计 Mac）

```bash
python tools/indesign_finalize.py --check-host          # 必须 match
```

产物一律写进 `idml/` 目录——那是 `release-manifest` 唯一采集的位置，
写进临时目录等于不被记录：

```bash
D=docs/_build/JE-1000F/US/idml
python tools/indesign_finalize.py \
  --idml    $D/manual_je1000f_us.idml \
  --indd    $D/manual_je1000f_us.indd \
  --pdf     $D/manual_je1000f_us_indesign.pdf \
  --report  $D/finalize_report.json
```

**验收**（对照主力机基线，不是"溢流清零"）：

- `missing_fonts` / `bad_links` 全空
- `pdf_export_validation.pass = true`
- `toolchain.version_pin_status = "match"`
- `page_count` / `story_count` 与基线相同
- `overset_stories` 的 story id 集合与基线**完全一致**（红 ⊞ 是设计内待办项，
  历史上从无 overset=0 的包，详见
  [`indesign_second_host_runbook.md`](indesign_second_host_runbook.md)）

## 7. parity（15.9pt 的验证证据）

```bash
D=docs/_build/JE-1000F/US/idml
python tools/idml_pdf_parity.py \
  --latex-pdf    ~/ref/"Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf" \
  --indesign-pdf $D/manual_je1000f_us_indesign.pdf \
  --preflight    $D/finalize_report.json \
  --manual-ir    $D/manual.ir.json \
  --reference-layout-plan $D/reference_layout_plan.json \
  --idml $D/manual_je1000f_us.idml \
  --indd $D/manual_je1000f_us.indd \
  --out  $D/parity_report.json
```

`--latex-pdf` 是历史参数名，**这里传的是已批准的参考 PDF**，不是新构建的
LaTeX PDF。阈值不必手传，契约已固化：300 dpi / 1537×2187 / 模糊 1px /
RGB MAD ≤ 0.008 / 变化像素比 ≤ 0.040 / 通道阈值 16。

**验收**：退出码 0，且报告中 `accepted = true`。任何一页不过即整体不过，
均值掩盖不了。

## 8. 收口：确认发布记录采集到了

```bash
python build.py release-manifest --config configs/config.us.yaml \
  --model JE-1000F --region US --data-root data/phase2
```

在最新的 `reports/releases/JE-1000F/US/en/manifests/<时间戳>.json` 中确认：

```
indesign_package.complete          = true
indesign_package.preflight.success = true
indesign_package.parity.accepted   = true
```

三项皆真，这一轮才算闭合。

## 9. 提交

需要入库的只有第 4 步改动的契约文件：

```bash
git add docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json
python tools/check_reference_layout_pins.py     # 必须 OK
```

`docs/_build/` 与 `reports/releases/` 均为本地产物，不提交。

## 10. 出错对照

| 现象 | 含义 |
| --- | --- |
| 第 4 步 `page_bindings` 非 0 | 版式真的变了 → 停，走审批而非重绑 |
| 第 5 步报 `identity.content` | 当前 target 的实际内容变了，走内容批准而非普通重绑 |
| 第 5 步报 `identity.assembly` | source 顺序、语言、页面角色或 composition map 变了，走装配批准 |
| 第 5 步报 `unclassified prose` | 批准 target 出现未登记页面角色；先补分类，禁止静默 prose fallback |
| 第 5 步报 `layout_params_sha256` | 有人改了 `data/layout_params.csv` 未刷 pin；CI 的 `reference-layout-pins` 作业现在会当场拦截 |
| 第 7 步某页不过 | 报告含逐页数值，那一页即该次几何改动的实际影响面 |

## 11. 本文的验证状态

2026-08-05 已用 52-source / 58-page 已批准 Manual IR 完成 v1→v2 原子迁移演练：
`page_bindings=0`、`composition_map=unchanged`、validation passed；原批准
snapshot hash 被保留为 provenance。v2 production 另需用一个不同 snapshot hash
但相同 target 内容的实时构建证明 provenance 漂移不再阻断。
