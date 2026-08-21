# JBP-2000B_US 入库单（骨架切片 S4，待操作者批准）

日期：2026-08-21 · 目标：`JBP-2000B_US`（Battery Pack 2000，HTP017，美加规）

来源唯一：出货说明书 `Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf`
（28 页 = 封面 + 前言 + 目录 + 3×8 正文 + 封底）。所有值逐字取自印刷页，
英/法/西三语分别取自 printed p07 / p15 / p23（规格+存储）、p02 / p10 / p18
（产品概览）、p03 / p11 / p19（操作）、p04 / p12 / p20（连接）。

本单**不含任何已执行的线上写入**。仓库侧改动已合在提交 `e18fff32`。

## 1. 为什么走这条路，而不是 `source_intake.py stage-plan`

技能文档里的克隆入库路径在这里走不通，原因有二，都在代码层：

- `build_staging_plan` 要求候选与姊妹机的逻辑键集**完全相等**（`missing or extra`
  直接抛错）。那是**区域克隆**的完整性门：同一产品换区域，结构不该变。加电包是
  **品类克隆**——21 行里取 11 行，且出货书把输入/输出合成一个 `INPUT/OUTPUT PORTS`
  段。我没有放宽这道门，因为它保护的是别的入库路径。
- 暂存表 `01_数据入库`（`tblIi0BEufjvGLIU`）只有一对本地化列 `行标签_ko` / `手册值_ko`
  （为韩规入库所建），payload 契约 `_STAGING_FIELDS` 同样只支持单一配对语言。
  加电包 US 需要 fr + es 两种。

因此本单充当暂存表的等价审核物：全部 20 行三语齐备、可 diff、逐行可批。
如果你更希望走暂存表，需要先在 `tblIi0BEufjvGLIU` 建 4 个字段
（`行标签_fr`/`手册值_fr`/`行标签_es`/`手册值_es`）——那是 schema 写入，同样要你批。

## 2. 已核实的前置事实（实查，非推断）

| 事实 | 结果 |
| --- | --- |
| `JBP-2000B_US` 主数据记录 | **已存在** `recvp853V23SP4`（US 区域，HTP017，`其他特色功能` 明写「双DC扩容口」），`Documents` 为空 |
| `03_内容源_规格参数明细` 中 JBP 行数 | **0** |
| `03_内容源_页面占位参数` 中 JBP 行数 | **0** |
| 需要的 13 个 `Row_key` | **全部命中** `02_主数据_参数名` 已有记录，无需新建 |
| `Slot_key` 语法 | `placement.variant.role`（`_parse_slot_key`），与现有 `side.pv.spec` / `side.car.spec` 同构 |
| 不可直写列 | `Row_key`/`region`/`Slot_key` 是 lookup，`document_key`/`source_row_key` 是 formula——必须靠 link 列驱动 |

## 3. 待写入清单

### 3.1 `02_主数据_Slot`（`tblS7qyV1DTZkoNq`）— 新建 4 条，须先做

出货书概览页有两个物理扩容口 A/B，每个带标签 + 一行「接扩展线端子 X」小注。
现有 17 个槽里没有 A/B 区分位。

| `Slot_label_source` | `Slot_key` | `Remark` |
| --- | --- | --- |
| 侧面扩容口 A 标签 | `side.a.label` | 加电包双扩容口 A（左侧视图） |
| 侧面扩容口 A 规格 | `side.a.spec` | 加电包扩容口 A 小注 |
| 侧面扩容口 B 标签 | `side.b.label` | 加电包双扩容口 B（左侧视图） |
| 侧面扩容口 B 规格 | `side.b.spec` | 加电包扩容口 B 小注 |

### 3.2 `03_内容源_规格参数明细`（`tblPUFJqt2uGGvTT`）— 新建 11 条

| # | 段 | S/R/L | Row_key | 行标签 en / fr / es | 值 en / fr / es |
| --: | --- | --- | --- | --- | --- |
| 1 | GENERAL INFO | 1/1/1 | `product_name` | Product Name / Nom du produit / Nombre del producto | Jackery Battery Pack 2000（三语同） |
| 2 | GENERAL INFO | 1/2/1 | `model_no` | Model No. / N° modèle / N° de modelo | JBP-2000B（三语同） |
| 3 | GENERAL INFO | 1/3/1 | `capacity` | Capacity / Capacité / Capacidad | 2048 Wh (40 Ah/51.2 V DC) / …51,2… / …51,2… |
| 4 | GENERAL INFO | 1/4/1 | `cell_chemistry` | Cell Chemistry / Cellule Chimique / Química Celular | LiFePO₄（三语同） |
| 5 | GENERAL INFO | 1/5/1 | `weight` | Weight / Poids / Peso | About 32.63 lbs/14.8 kg / Environ 32,63 lbs / 14,8 kg / Aproximadamente 32,63 libras/14,8 kg |
| 6 | GENERAL INFO | 1/6/1 | `dimensions` | Dimensions / Dimensions / Dimensiones | 14.37 × 10.04 × 7.52 in / 36.5 × 25.5 × 19.1 cm（fr 用 `po`、es 用 `pulgadas`，小数点改逗号） |
| 7 | GENERAL INFO | 1/7/1 | `cycle_life` | Cycle Life / Durée de vie / Ciclo de vida | 6000 cycles to 70%+ capacity / Capacité de 6000 cycles à 70 % ou plus / 6000 ciclos de carga hasta 70 % + de capacidad |
| 8 | INPUT PORTS | 2/1/1 | `dc_expansion_port` | DC Expansion Port (Input) / Port d’extension CC (Entrée) / Puerto de Expansión de CC (Entrada) | 36.8V-57.6V⎓75A Max / 36,8V-57,6V⎓75A Max / 36,8 V-57,6 V⎓75 A Máx. |
| 9 | OUTPUT PORTS | 3/1/1 | `dc_expansion_port` | DC Expansion Port (Output) / …(Sortie) / …(Salida) | 同上（输出口也是 75A） |
| 10 | ENVIRONMENTAL OPERATING TEMPERATURE | 4/1/1 | `charging_temperature` | Charge Temperature / Température de charge / Temperatura de carga | 14°F to 113°F / -10°C to 45°C（三语同值，分隔符本地化） |
| 11 | ENVIRONMENTAL OPERATING TEMPERATURE | 4/2/1 | `discharging_temperature` | Discharge Temperature / Température de décharge / Temperatura de descarga | 同上 |

### 3.3 `03_内容源_页面占位参数`（`tblEhqJVXiyKtnwq`）— 新建 9 条

| # | Page | 段 | S/R/L | Row_key | Slot_key | 值 en / fr / es |
| --: | --- | --- | --- | --- | --- | --- |
| 12 | Product overview | CONTROLS | 7/1/1 | `main_power_button` | `label` | POWER button / Bouton d’alimentation principale / Botón de encendido principal |
| 13 | Product overview | OUTPUT PORTS | 3/1/1 | `dc_expansion_port` | `side.a.label` | DC Expansion Port A / Port d’extension CC A / Puerto de expansión A de CC |
| 14 | Product overview | OUTPUT PORTS | 3/1/1 | `dc_expansion_port` | `side.a.spec` | (Connect to Expansion Cable Terminal A) / (Connexion à la borne A du câble de rallonge) / (Conectar a la Terminal A del Cable de Expansión) |
| 15 | Product overview | OUTPUT PORTS | 3/2/1 | `dc_expansion_port` | `side.b.label` | DC Expansion Port B / …CC B / Puerto de expansión B de CC |
| 16 | Product overview | OUTPUT PORTS | 3/2/1 | `dc_expansion_port` | `side.b.spec` | (Connect to Expansion Cable Terminal B) / …borne B… / …Terminal B… |
| 17 | operation_guide | SETTINGS | 8/1/1 | `default_standby_duration` | `value` | 2 hours / 2 heures / 2 horas |
| 18 | storage | ENVIRONMENTAL… | 4/1/1 | `storage_temperature` | —（`Param`=1 month/1 mois/1 mes） | -4°F to 113°F / -20°C to 45°C (0-60%RH) |
| 19 | storage | ENVIRONMENTAL… | 4/1/2 | `storage_temperature` | —（3 months/3 mois/3 meses） | 32°F to 113°F / 0°C to 45°C (0-60%RH) |
| 20 | storage | ENVIRONMENTAL… | 4/1/3 | `storage_temperature` | —（12 months/12 mois/12 meses） | 32°F to 77°F / 0°C to 25°C (0-60%RH) |

### 3.4 `03_内容源_Manual_Copy_Source`（`tblboUMUiLbWk9nF`）— 新建 1 条 + TM 配对

概览页面板标题走 copy 表 + TM 派生。加电包用 **LEFT SIDE VIEW**，主机是 RIGHT SIDE VIEW。

- 新 copy 行：`copy_key=product_overview.left_side_view`、`copy_type=panel_title`、
  `page_id=product_overview`、`Market=ALL`、`Model=ALL`、`Source_lang=en`、
  `source_text=LEFT SIDE VIEW`、`Is_Latest=TRUE`、`Version=V1.0`
- TM 需有 `LEFT SIDE VIEW` → fr `VUE LATÉRALE GAUCHE`、es `VISTA LATERAL IZQUIERDA`

**这条会静默失败，不会报错**：`build_spec_title_rows` 与 copy 本地化都是
`translated or source_text`——TM 缺译时直接回落英文原文。结果是法语页和西班牙语页
印英文面板标题，构建全绿。所以 TM 配对必须与 copy 行同批写。

### 3.5 后续（本单不含，S4 剩余）

- `03_内容源_TROUBLESHOOTING`：8 个故障码（F0 / F1,F2 / F3 / F4 / F5 / F6-F9,FA,FC / FF），
  出货书 printed p05 / p13 / p21
- `03_内容源_LCD icons`：电量百分比/故障码 + 充电指示，printed p03 / p11 / p19

## 4. 待你裁决的三件事

1. **合并段标题**。出货书印一个 `INPUT/OUTPUT PORTS`；我把两条扩容口行分别放进主机
   已有的 `INPUT PORTS` / `OUTPUT PORTS`，因为 `Section` 单选没有这个选项，
   而段标题文字另在 `spec_titles.csv`（由 copy 表 + TM 派生）。代价是规格页会印两个
   段标题而非一个。要改成真正合并需：`Section` 两张表各加一个选项 + 一条 copy 行 + TM 配对。
   按你「印不出来可以放 InDesign」的口径，这一处更像手工层承担项，故默认不改。
2. **西语数字排版分叉**。出货书西语印 `-20 °C a 45 °C (0-60 % HR)`（单位前带空格），
   主机 `JE-2000E_US` 现有西语行是 `-20°C a 45°C (0-60% HR)`（无空格）。本单按**出货书原样**写，
   这样 S6 逐页对账应为零差异；代价是与主机既有西语惯例不一致（属语言资产治理账）。
3. **行标签与主机分叉**。出货书印 `Charge Temperature` / `Discharge Temperature`，
   主机印 `Charging` / `Discharging`。同一 `Row_key`，标签不同。本单按出货书写。

## 5. 顺便查到的一条主机数据缺口

姊妹机 `JE-2000E_US` 的 `storage_temperature` 三行与 `default_standby_duration` 行
**`Value_fr` 为空**（`Value_es` 有值）。加电包这四行的法语值出货书里有，本单已填，
因此加电包数据比姊妹机更完整。主机的法语缺口不在本单范围，建议另开。

## 6. 执行与验证顺序

```
1. 3.1 建 4 条 Slot 记录 → 回读拿 record_id
2. 用这 4 个 id 补全占位 payload 的 Slot_key_link
3. 3.2 写 11 条规格行 → 逐条 GET 回读，报 record_id + source_row_key
4. 3.3 写 9 条占位行 → 同样逐条回读
5. 3.4 写 copy 行 + TM 配对 → 回读
6. python build.py sync-data（把线上写入拉进 data/phase2 镜像）
7. python build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US
```

第 7 步的当前基线：`FAILED with 30 issue(s)`，全部是
`MISSING_REQUIRED_SPEC_ROW`（10 类需求 × 3 语言），契约与模板零问题。
写入 + sync 后应归零。

回滚：全部为新建记录，record_id 会逐条记录，可单条删除；模板与契约改动 `git revert`。

## 7. 本单发现的、S4 范围外的三处缺口

- **插图 3 张未入库**：加电包正面图、左侧视图、堆叠间距图；`connections/*` 类别下
  一个资产都没有。模板已用 `TODO(资产)` 标注源页，未引用不存在的 asset key
  （那会让构建硬失败）。无字化提取需要 `.ai` 母版，出货 PDF 不够。
- **概览 geometry 只有一个实例**：`overview_component_instances.json` 仅
  `je1000f-us-v1`（钉 JE-1000F/US），`resolve_overview_instance` 对无匹配目标直接抛
  `ComponentSpecError`。HTML 与 IDML 的概览投影因此暂无加电包实例；PDF 与 Word 不走这条路。
  补 geometry 要碰参考版式契约，本切片视为红线。
- **checklist 的 S4 条目需更正**：写的是「`connections` 和 `installation` 两个模板」，
  但骨架里没有 `installation` 槽，真正缺的是 **10 个**模板（toc 1 + 概览 3 + 连接 3 + 操作 3）。
