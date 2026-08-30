# IDML candidate → production 晋升流程

每条新产线的 IDML 装配都会走到同一扇门前：candidate 装配合同能出包、能交付
InDesign 手工层,但在视觉验收通过并**晋升为批准参考版式合同**之前,它永远不是
production。此前这条流程只有 `configs/config.bp-us.yaml` 里的一句注释;本文是
成文版。JBP-2000B_US 是第一个走到这扇门的目标,之后每条产线都会重复这条路。

配套阅读:[`style_component_usage_guide.md`](style_component_usage_guide.md)
§7 的八步产线配方(本文接管其第 8 步)、
[`component_reuse_survey.md`](component_reuse_survey.md) D3(语言三集合)。

## 1. 两种合同,一个解析阶梯

`tools/idml/ir_projection.py::build_reference_page_plan` 按固定顺序解析装配来源:

1. **批准参考版式合同**(approved)——经
   `docs/renderers/contracts/reference_layout_registry.json` 注册发现,
   按 (model, region) 匹配。命中即用,且校验失败就报错,不回落。
2. **candidate 目标装配合同**——family config 里 `paths.idml_assembly_plan`
   (整份 config)或 `paths.idml_assembly_plans`(`{Document_Key: path}`,按
   `<MODEL>_<REGION>` 选中;二者互斥)显式指定(`tools/build_paths.py::
   resolve_idml_assembly_plan`,无文件名/型号自动发现)。
3. **测量式 LaTeX 页面计划**——都没有时,从参考 PDF 现测。

| | candidate | production(approved) |
|---|---|---|
| schema | `target-idml-assembly-plan/v1` | `approved-reference-layout-plan/v2` |
| 存放 | `docs/renderers/contracts/target_assembly/` | `docs/renderers/contracts/reference_layout/` |
| 发现方式 | config 显式 opt-in | registry 注册,自动发现 |
| 加载器 | `tools/idml/target_assembly_plan.py` | `tools/idml/reference_layout_plan.py` |
| `plan_source` | `target-assembly` | `approved-reference` |
| 组件严格性 | `strict_component_assets=False`(缺令牌/缺资产走回退) | `True`(合同令牌与资产 fail-closed) |
| 结构标记 | 原生矢量结构占位(包可读) | 无(交付态) |
| 状态声明 | `status: "candidate"` + `production_eligible: false`,**二者缺一加载即拒** | `approval.status: "approved"` + `approved_by/approved_at/method`,缺一校验即拒 |

candidate 加载器的 fail-closed 是**防偷跑**设计
(`target_assembly_plan.py::_validate` 顶部两条):没人能把一个 candidate JSON
改一个布尔值就当 production 用——晋升必须走下面的换合同流程。

## 2. 晋升前置条件(验收门,全部操作者裁决)

1. **结构对账通过**——产线的 S6 式对账报告(shared composition 全命中、
   结构性分歧清零、与手册书逐页对照),参照 BP 的
   `code-as-doc/reviews/jbp2000b_us_s6_reconciliation_2026-08.md`(PR #959)。
2. **InDesign 原生轮完成**——操作者用交付 zip(Links 相对化)在 InDesign
   打开、finalize、导出 PDF;视觉验收以**这份导出 PDF** 为对象。
3. **参考 PDF 定稿**——视觉验收通过的那份 PDF 就是合同里
   `reference_pdf` 的本体(sha256/byte_size/page_count/page_size_pt/
   PDF/X 与 output intent 全部入合同)。此后它是该目标的像素基准。

## 3. 晋升步骤

### 3.1 起草 approved v2 合同

以 [`je1000f_us_v2_20260605.json`](../../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json)
为模板,从 candidate 迁移数据。命名沿用 `<target>_v<N>_<yyyymmdd>.json`。

字段迁移表(candidate → approved v2):

| 字段 | 处理 |
|---|---|
| `pages[].composition_id / language / page_count / source_ref / start_page` | 原样保留 |
| `pages[].composition_type / page_role` | **丢弃**(approved 侧由 `composition_id` 词汇表与页面角色分类器推导) |
| `pages[].source_sha256` | **新增**——每页源 RST 的内容指纹,rebind 工具回填 |
| `status / production_eligible` | 删除,换 `approval` 块(§3.2 由 rebind 写入) |
| `reference_pdf` | 从"逻辑指纹"升级为完整身份(§2 第 3 条的那份 PDF) |
| `render_contract` | **新增,人工定值**——光栅对比公差(dpi、ICC、模糊、MAD、变化像素比)。从 JE 值起步,首轮 parity 跑完再收紧 |
| `idml_contract` | **新增,人工定值**——`max_skipped_raw`、整页链接禁令、`editable_components` 可编辑性门、`allowed_unclassified_source_refs` |
| `identity` | 四组 pin(content/assembly/style/provenance),不要手写——§3.2 |

目前**没有自动转换器**;字段迁移是机械的,`render_contract` 与
`idml_contract` 是判断项。BP 首晋升时若想固化,记债一个
`tools/promote_target_assembly.py`。

### 3.2 绑定 identity pins(rebind 工具,勿手算)

```bash
python tools/reference_layout_rebind.py \
  --plan docs/renderers/contracts/reference_layout/<target>_v1_<date>.json \
  --manual-ir docs/_build/<MODEL>/<REGION>/idml/manual.ir.json \
  --approved-by <操作者> --approval-method native-indesign-pdf-review \
  --write
```

默认 dry-run;`--write` 原子替换。内容指纹与现存 pin 不一致时需要显式
`--approve-content-change`——这就是"重批"语义,不要为了让命令通过而加它。

### 3.3 注册进 registry

在 [`reference_layout_registry.json`](../../docs/renderers/contracts/reference_layout_registry.json)
的 `plans` 追加一行:`target.model / target.region / target.languages` +
`path`。`languages` 是合同语言全集,顺序即校验顺序。

**不注册不是"暂时不生效"而是报错**:`reference_layout_plan.py::
_unregistered_approved_contracts` 会在校验时发现 reference_layout 目录里
存在同族未注册合同并直接失败——批准合同不允许静默降级回测量路径。
(candidate JSON 留在 `target_assembly/` 目录不受此扫描影响,可原样归档。)

### 3.4 退役 config 的 candidate 行

解析阶梯里 approved 优先,config 的 candidate 指向从此是死配置——同一 PR 里
删掉它和旁边的 candidate 注释,避免下一个读 config 的人误判产线还停在
candidate 阶段。单数形(`paths.idml_assembly_plan`,见 `configs/config.bp-us.yaml`)
整键删除;共享 family config 的按目标形(`paths.idml_assembly_plans`,见
`configs/config.kr.yaml` 三个 KR 型号共用一份 config)**只删本目标那一行**,
该键上其他型号的行必须留着。

`paths.idml_layout_params_overlays*` **不在此列**——批准几何就长在那些
`lang_<code>_` 行里(见 §4 strict 翻转),删掉会让已进 `contract_languages`
的语言直接构建失败。

## 4. 晋升的直接后果(strict 翻转清单)

`plan_source` 变为 `approved-reference` 后,`export_idml.py` 以
`strict_component_assets=True` 建 writer,以下从"回退"变"报错":

- **组件合同令牌** fail-closed:每个 approved 组件的必需 layout 令牌
  缺行/空值/非数值直接抛错(`component_param_pt(strict=True)`)。晋升前用
  产线的结构闸门 + 一次 strict 试跑清点缺口。
- **语言覆盖行合同**(#961 起的三集合语义):目标语言若要求覆盖行成为合同
  (批准几何长在 `lang_<code>_` 行里),把该语言加进对应组件的
  `contract_languages` 声明;新语言产线同时评估是否进
  `governed_languages()`(流程行为门)——这两个决定都属于晋升,不是级联
  接线。
- **组件资产** fail-closed:按钮/图标等 bundle 资产缺失从"降级为通用表格"
  变为构建失败。
- **像素与结构 parity 生效**:`render_contract` 公差进 parity 门,
  `check_reference_layout_pins.py` 开始盯 pin 漂移(修复命令即 §3.2 的
  rebind;pin 漂移的历史教训见 2026-07 参考版式 pin 漂移事故)。
- **原生结构占位标记关闭**(交付态不再带 target-assembly 的矢量占位)。

## 5. 晋升 PR 的验收清单

- [ ] §2 三个前置条件有据可查(对账报告链接 + 操作者验收记录)
- [ ] 新合同通过 `validate_page_plan`(跑一次目标 IDML 构建即触发)
- [ ] registry 行与合同 `target` 一致;`--all-registered` dry-run 干净
- [ ] config 的 candidate 指向已退役(单数形删整键;`idml_assembly_plans` 只删本目标那一行、保留其他型号),`idml_layout_params_overlays*` 保持不动
- [ ] strict 试跑通过(全部合同令牌与资产就位)
- [ ] golden / 结构闸门按需主动重基线,PR 里逐项交代
- [ ] 晋升本身是操作者门:PR 由操作者合入,不适用 gate-on-green 自合
