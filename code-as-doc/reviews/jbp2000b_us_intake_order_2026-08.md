# JBP-2000B_US 入库单（骨架切片 S4，待操作者批准）

日期：2026-08-21 · 目标：`JBP-2000B_US`（Battery Pack 2000，HTP017，美加规）

来源唯一：出货说明书 `Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf`
（28 页 = 封面 + 前言 + 目录 + 3×8 正文 + 封底）。所有值逐字取自印刷页，
英/法/西三语分别取自 printed p07 / p15 / p23（规格+存储）、p02 / p10 / p18
（产品概览）、p03 / p11 / p19（操作）、p04 / p12 / p20（连接）。

本单**不含任何已执行的线上写入**。仓库侧改动已合在提交 `e18fff32`。

## 1. 为什么走这条路，而不是 `source_intake.py stage-plan`

> **本节已更正（2026-08-21，经对抗性复核 + 实跑 `build_staging_plan`）。**
> 初版写的是「克隆入库路径走不通」。那是错的，下面是核实后的版本。

`stage-plan` **技术上跑得通**，但跑通的代价是毁掉这道门本身的审计价值。

`build_staging_plan` 的键集相等检查（`source_intake_staging.py:286-294`）比的是
**调用方喂进来的两份 JSON**，不是与线上表的实际比对。所以把姊妹机导出裁成 11 行再喂进去，
门就放行。实跑确认：

```
>>> build_staging_plan SUCCEEDED with a trimmed sibling
    row_count   : 11
    completeness: complete: 11 rows cover region siblings (11)
```

问题就在最后那行。它**宣称"完整"**——而那个 11 是相对我自己裁出来的基线算的。
计划里没有任何字段记录被丢掉的 10 行姊妹机行。也就是说，手工裁剪姊妹机导出会把一次
**子集克隆洗成一次完整克隆**，静默绕过技能文档硬门 2。真正缺的不是能力，是
**显式的子集/品类克隆模式 + 一份记录在案的排除清单**。

本地化语言那条我也写错了地方。`_STAGING_FIELDS` 只带一对语言列是事实
（线上 `tblIi0BEufjvGLIU` 确实只有 `行标签_ko` / `手册值_ko`，实查 18 个字段，
两列的字段说明写明「KR目标」），但那不是墙。真正的边界在下游：
`agent/wukong-bridge/intake_commit_driver.py` 只读 `手册值_ko` / `行标签_ko`（:399,401），
对目标行上任何其它本地化列**主动发警告**并明写
「本次未同步这些本地化值，本地化值需人工同步（技能硬门 5）」（:426-435）。
所以 fr/es 走人工从来就是**设计意图**，不是工具短板——暂存层只承载源语言结构（可选加 ko）。

结论不变，理由更新：本单充当暂存表的等价审核物（20 行三语齐备、可 diff、逐行可批），
选它不是因为 `stage-plan` 不能跑，而是因为在有显式子集模式之前，用 `stage-plan`
会让这次入库对着一份假的完整性声明过门。若要改走 `stage-plan`，先给它加子集模式
（带排除清单落盘），fr/es 仍按硬门 5 人工写正式表。

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

## 5. 顺便查到的两件主机线问题（不在本单范围，建议各开一单）

初版本节只说「`JE-2000E_US` 四行缺 `Value_fr`」。查全后是下面两件，第二件比第一件严重。

### 5.1 `JE-2000E_US` 与 `JE-2000F_US` 各缺同样的 18 行法语值

不是四行。两个目标缺的是**完全相同的 18 行**（0 条独有），全部是占位行，规格页一行不缺——
系统性缺口，不是录入疏漏。`_pick_lang_value`（`utils/spec_master_row_helpers.py`）对
`Value` 基名的键序是 `Value_fr` → … → `Value_source`，取第一个非空，所以空法语
**回落成英文原值**，构建全绿无告警。

`origin/review/JE-2000E-US`（PR #494）的法语概览页实际印成：

```
* - **DC/USB Power Button**        ← 法语块里的英文
* - **USB-C 30W Output**           ← 英文
* - **USB-A 18W Output**           ← 英文
  - **Sortie CA**
    120 V~ 60 Hz, 12,5 A max., 1500 W Nominal    ← 法语正常
* - **Total Output**               ← 英文（应为 Sortie totale）
```

存储行是**法英混排**：`1 mois : -4°F to 113°F / -20°C to 45°C (0-60%RH)`——月份取到法语，
温度串回落英文（`to` 不是 `à`、`RH` 不是 `HR`）。同行西语是完整的
`1 mes: -4°F a 113°F / -20°C a 45°C (0-60% HR)`。

**欧规姊妹机的法语不能直接复制过来。** 17/18 在 `*_EU` 里有法语，但绝大多数值本身不同：
欧规存储行是纯公制 `-20 °C à 45 °C`（美规要带华氏）、`ups_bypass_output` 欧规 `10 A`
对美规 `12A (1440W)`（230V vs 120V 体系）、USB-C 高功率口欧规 140W 对美规 100W。
只有 3 条是干净复制（`Sortie totale`、`2 heures`、`12 heures`）；其余 14 条欧规只能提供
**措辞范式**（`max.` 缩写、逗号小数、`à`、`HR`）；`usb_c_high_power_port` 欧规无对应行。

### 5.2 `JE-2000E_US` / `JE-2000F_US` 概览页印着另一个型号的电气额定值

同一本书自己跟自己矛盾，已在 `origin/review/JE-2000E-US`（PR #494）的产物里坐实：

| 页面 | 印的是 |
| --- | --- |
| 规格页 | `4 × AC \| 120V~ 60Hz, 20A Max, 2400W Rated per port, 2400W in Total, 4800W Surge Peak` |
| 概览页 | `Total Output \| 1500W Rated, 3000W Surge Peak` · `120V~60Hz, 12.5A, 1500W Rated` |

`JE-2000E` 是 HomePower 2000 Plus，主数据额定 2400W（峰值 4800W），欧规姊妹机概览页印的
也是 `2400 W Rated, 4800 W Surge Peak`。美规概览页那三个数 `1500W / 3000W / 12.5A`
**逐字等于 JE-1000F 的值**——概览占位行是从 1000F 那条线复制未改。

`JE-2000F_US` 同病：概览页 1500W/3000W，欧规姊妹机 2200W/4400W，主数据 2200W（峰值 4400W）。
附一条需工程确认：`JE-2000F_US` 规格页印 2400W，与其主数据 2200W 也不一致——这条我不敢判哪个对。

规格页对、概览页错，两页在同一本书里，所以这不是缺数据，是**印了另一个型号的规格**，
且已在 review 中。正确值需对着规格书由工程确认后再写，不在本单范围。

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
- **概览 geometry 不是阻塞点——别去改那个文件**（本条初版写反了，经对抗性复核更正）。
  registry 与 resolver 的事实没错：`overview_component_instances.json` 只有
  `je1000f-us-v1`（钉 JE-1000F/US），`resolve_overview_instance` 对无匹配目标确实抛
  `ComponentSpecError`（只在 model 与 region **都**为空时才回落 `default_instance_id`）。
  但对 `JBP-2000B/US`，**HTML 和 IDML 都根本不会走到这个 resolver**：
  - HTML：`web_manual.json` 的 `figure_targets` 只列 `JE-1000F/US`，所以
    `transform_web_fragment` 原样返回片段（`web_presentation.py:1686-1687`），概览分支是
    静默软跳过。而且该调用点传的是显式 `instance_id`（`web_manual.json:81`），
    `overview_instance.py:303-307` 在 instance_id 存在时**忽略 model/region**——这条路
    永远不会因目标不匹配而抛错，只会把 JE-1000F 的 geometry 套到任意型号上。
  - IDML：`export_idml.py:377` 要求 `plan_source == "approved-reference"`
    （`:234-236`），只有 `reference_layout_registry.json` 里那唯一一份 JE-1000F/US 计划
    能产生它。所以 `add_product_overview_page`（含 `page_overview.py:368` 的 resolver 调用）
    对加电包永远到不了，概览页降级为普通文流。

  要真正立起加电包的概览合成，顺序是：(1) 补两张缺失插图 → (2) 给 HTML 在
  `web_manual.json` 加 `figure_targets` 行 → (3) 给 IDML 做批准版式计划 + registry 行
  → (4) 才轮到在 `overview_component_instances.json` 加 BP 实例。**只做 (4) 什么都不会变。**

  PDF 与 Word 不走 registry 这个结论成立，但我初版给的机制是错的：
  `HBOverviewPanel` / `HBOverviewPair` **不是 draft 引擎生成的**，而是欧规家族模板里
  手写的 `.. raw:: latex` 块（`page_eu-en|fr|es|de|it|uk|kr/03_product_overview*.rst`；
  韩规模板归在 `page_eu-kr`，这是我误判的来源）。代码里唯一出现该宏的地方是
  `component_specs/overview_adapters.py:107` 的 `latex_overview_projection`，
  它没有生产调用方（只有测试）。US/JP/ZH/BP 概览模板出的是普通
  `.. image::` + `.. list-table::`。
  补 geometry 要碰参考版式契约，本切片视为红线。
- **checklist 的 S4 条目需更正**：写的是「`connections` 和 `installation` 两个模板」，
  但骨架里没有 `installation` 槽，真正缺的是 **10 个**模板（toc 1 + 概览 3 + 连接 3 + 操作 3）。
