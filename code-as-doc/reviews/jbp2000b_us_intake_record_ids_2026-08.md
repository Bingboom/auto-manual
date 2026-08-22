# JBP-2000B_US 入库 record_id 台账

执行日期：2026-08-22 · 授权：操作者「1确认入库」
基座：`LD3lb4G1ua4GOVs1vxAc9W2enje`（文档构建）· 身份：`--profile cli_aaa0db0d4b39dcca --as bot`
批次全部为**新建**（无更新、无删除），除 §4 一处 TM 字段更新。

回滚方式：逐条 `base +record-delete --record-id <id> --yes`；§4 那条是字段回改，原值见该节。

## 1. `02_主数据_Slot`（`tblS7qyV1DTZkoNq`）— 4 条新建

表行数 17 → 21。

| record_id | Slot_key | Slot_label_source |
| --- | --- | --- |
| `recvsZelIAkzOH` | `side.a.label` | 侧面扩容口 A 标签 |
| `recvsZelIAvx2D` | `side.a.spec` | 侧面扩容口 A 规格 |
| `recvsZelIAVvjV` | `side.b.label` | 侧面扩容口 B 标签 |
| `recvsZelIAGMSH` | `side.b.spec` | 侧面扩容口 B 规格 |

## 2. `03_内容源_规格参数明细`（`tblPUFJqt2uGGvTT`）— 11 条新建

全部回读确认：lookup（`Row_key`/`region`）与 formula（`document_key`/`source_row_key`）均正确解析，三语齐备。

| record_id | source_row_key |
| --- | --- |
| `recvsZeCTfMv4S` | `JBP-2000B_US__v1.0__specifications__s01__r01__product_name__main__l01` |
| `recvsZeCTf7hLp` | `…__s01__r02__model_no__main__l01` |
| `recvsZeCTfXo8D` | `…__s01__r03__capacity__main__l01` |
| `recvsZeCTfT6Iv` | `…__s01__r04__cell_chemistry__main__l01` |
| `recvsZeCTfWyEv` | `…__s01__r05__weight__main__l01` |
| `recvsZeCTfcOCR` | `…__s01__r06__dimensions__main__l01` |
| `recvsZeCTf4xu4` | `…__s01__r07__cycle_life__main__l01` |
| `recvsZeCTfbPIW` | `…__s02__r01__dc_expansion_port__main__l01`（INPUT PORTS） |
| `recvsZeCTf7oCS` | `…__s03__r01__dc_expansion_port__main__l01`（OUTPUT PORTS） |
| `recvsZeCTfcyWn` | `…__s04__r01__charging_temperature__main__l01` |
| `recvsZeCTfMzTP` | `…__s04__r02__discharging_temperature__main__l01` |

## 3. `03_内容源_页面占位参数`（`tblEhqJVXiyKtnwq`）— 9 条新建

`Slot_key_link` 六条全部**确认落库**（record-link 有静默不持久的先例，本次未触发）。

| record_id | source_row_key |
| --- | --- |
| `recvsZeLXql874` | `…__Product_overview__s07__r01__main_power_button__label__l01` |
| `recvsZeLXqJr7v` | `…__Product_overview__s03__r01__dc_expansion_port__side.a.label__l01` |
| `recvsZeLXqRXFo` | `…__Product_overview__s03__r01__dc_expansion_port__side.a.spec__l01` |
| `recvsZeLXq8VN3` | `…__Product_overview__s03__r02__dc_expansion_port__side.b.label__l01` |
| `recvsZeLXqwNn2` | `…__Product_overview__s03__r02__dc_expansion_port__side.b.spec__l01` |
| `recvsZeLXqr3h2` | `…__operation_guide__s08__r01__default_standby_duration__value__l01` |
| `recvsZeLXqnZei` | `…__storage__s04__r01__storage_temperature__main__l01`（1 month） |
| `recvsZeLXqgmok` | `…__storage__s04__r01__storage_temperature__main__l02`（3 months） |
| `recvsZeLXqzGmz` | `…__storage__s04__r01__storage_temperature__main__l03`（12 months） |

## 4. copy 行与 TM

- `03_内容源_Manual_Copy_Source`（`tblboUMUiLbWk9nF`）新建 1 条：**`recvsZf31qkQuo`**
  `copy_key=product_overview.left_side_view`、`copy_type=panel_title`、
  `page_id=03_product_overview`（注意不是入库单里猜的 `product_overview`）、
  `Market=ALL`、`Model=ALL`、`Source_lang=en`、`source_text=LEFT SIDE VIEW`。

- Translation_Memory 句对表（base `Ji1hb5ub1aUbewsTljGccvx5nhc` / `tblqtvNbgjDwR4ya`）
  **更新** 1 条：`recvgEwErzRgMF`（`en=LEFT SIDE VIEW`）。入库单假设需要新建，实际该行已存在。
  改了三个字段：

  | 字段 | 原值 | 新值 | 理由 |
  | --- | --- | --- | --- |
  | `用途标签` | *(空)* | `["manual_copy"]` | `_is_manual_copy_tm_row` 要求含此标签，缺它则整行对 copy 本地化不可见 |
  | `fr` | `Vue latérale gauche` | `VUE LATÉRALE GAUCHE` | 出货书与姊妹行 `RIGHT SIDE VIEW` 均为全大写；入库单 §3.4 指定的也是全大写 |
  | `es` | `Vista lateral izquierda` | `VISTA LATERAL IZQUIERDA` | 同上 |

  `de` / `it` 原本已是全大写，`ko` 无大小写，未动。

  **这一条值得单独记住**：标签缺失是静默失效。打标签之前，`Localized_Copy.csv` 里
  `left_side_view` 的九个语言列**全是英文原文** `LEFT SIDE VIEW`，构建全绿，唯一信号是
  没有任何闸门读取的 `reports/content_audit/manual_copy_missing_translations.csv`。

## 5. 同步与验证结果

`build.py sync-data` 后：`Spec_Master.csv` 978 → 998 行，`Manual_Copy_Source.csv` 25 → 26 行。

`build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US`：

- `validate_spec_master` 从 **30 条 `MISSING_REQUIRED_SPEC_ROW` → OK**
- 能力门按预期裁掉 `ups_mode` 与 `extra_battery`（`UPS功能`/`加电包扩容` 均为 FALSE），三语共 6 个片段
- 构建随后停在 `symbols page has no matching rows` —— 即入库单 §3.5 明确划为「本单不含」的
  csv_page 内容，见下节

缺译报告从 9 条降到 4 条（`zh`/`jp`/`pt-BR`/`uk`——加电包不构建这四种语言，属潜在债）。

## 6. 下一批（尚未入库）

三张 csv_page 源表都按 `Model` 列匹配，均不含 `JBP-2000B`：

| 表 | 现状 | 加电包需要 |
| --- | --- | --- |
| `03_内容源_Symbols`（`tblSZX8hBzpJLqAe`） | 17 行，`Model` 列九个主机型号 | 出货书 printed p01 的符号集；`Model` 列加入 `JBP-2000B` |
| `03_内容源_LCD icons`（`tblW5fCuJ6YdAcND`） | 27 行 | 只有电量百分比/故障码 + 充电指示两项（printed p03），远少于主机 27 项 |
| `03_内容源_TROUBLESHOOTING`（`tblOmJoAfU35brkb`） | 45 行，`Model` 为 `ALL` 或 `JE-2000E` | 8 个码：F0 / F1,F2 / F3 / F4 / F5 / F6-F9,FA,FC / FF（printed p05） |

**第二批已于 2026-08-22 执行完毕，见 §7。**

---

## 7. 第二批：三张 csv_page 源表（2026-08-22，操作者授权）

授权来源：操作者对
`code-as-doc/reviews/jbp2000b_us_csvpage_intake_order_2026-08.md` 的五项裁决，
其中「改这 11 行 Model」与「照 FR/ES 新写一句英文」为明确授权。

### 7.1 前置：两处 schema 写入（Model 多选加选项）

`JBP-2000B` 原本不是选项，写入会被拒。用 `+field-update` 做整份 options 的 PUT。
**回读确认：零选项丢失、零颜色改动。**

| 表 | 字段 | 选项数 |
| --- | --- | --- |
| `03_内容源_Symbols` | `fld3OoJRQc` | 10 → 11 |
| `03_内容源_LCD icons` | `fldjINVVwM` | 9 → 10 |

踩坑记录：`+field-update` 的 payload 是**扁平**的
`{"name":…,"type":"select","multiple":true,"options":[…]}`。用数字 type 码会报
`Invalid discriminator value`，包一层 `property` 会报 `Unrecognized key(s) in object: 'property'`。

### 7.2 `03_内容源_Symbols` — 11 条编辑（只改 `Model`）

回读逐条确认：`JBP-2000B` 在册、**文本一字未动**、`weee2`（`rec277z0GFV87J`）未被误 widen。

| record_id | symbol_key | Model 数 |
| --- | --- | --- |
| `rec277z0GFV6DG` | `warning_triangle` | 9 → 10 |
| `rec277z0GFV6T6` | `read_manual` | 9 → 10 |
| `rec277z0GFV738` | `electric_shock` | 7 → 8 |
| `rec277z0GFV7aQ` | `battery_charging` | 7 → 8 |
| `rec277z0GFV7ii` | `explosive_material` | 7 → 8 |
| `rec277z0GFV7pR` | `heavy_object` | 7 → 8 |
| `rec277z0GFV7wT` | `do_not_dismantle` | 9 → 10 |
| `rec277z0GFV7Ej` | `no_open_flame` | 9 → 10 |
| `rec277z0GFV7LR` | `keep_away_from_children` | 9 → 10 |
| `rec277z0GFV7Te` | `li_ion` | 9 → 10 |
| `rec277z0GFV80p` | `weee` | 9 → 10 |

回滚：把 `Model` 里的 `JBP-2000B` 去掉即可。

### 7.3 `03_内容源_LCD icons` — 2 条新建

| record_id | No. | icon_en |
| --- | --: | --- |
| `recvsZG5nwlwlq` | 1 | Power Percentage/Fault Code |
| `recvsZG5nwQVVQ` | 2 | Charging Indicator |

两处按裁决执行、都不是纯转录，**必须留痕**（已写进两行的 `备注` 字段）：

1. **`recvsZG5nwlwlq` 的 `icon_desc_en` 含一句新撰英文**：
   `If code FF appears, remove the load and the product may recover by itself; if it does not,
   please contact Jackery Customer Support. If any other code appears, please contact Customer Support.`
   出货书 EN 原文**没有**这句，是照 FR/ES 新写的（操作者 2026-08-22 批准）。
2. **ES 印刷错字已修正**：`Jackery.En caso` → `Jackery. En caso`。

**一处有意保留的矛盾**：出货书自身对 FF 给了两种处置——本页（printed 03）说移除负载可自恢复，
故障排除页（printed 05）说置于适温环境。按操作者裁决（路线 A）照实保留，
**留待 S6 逐页对账时识别，不要当成回归**。

### 7.4 `03_内容源_TROUBLESHOOTING` — 7 条新建 + 11 条收窄

表行数 45 → 52。

新建（`Model=JBP-2000B`、`Region=US`）：

| record_id | No. | error_code |
| --- | --: | --- |
| `recvsZGkFOBPrG` | 1 | `F0` |
| `recvsZGkFOEQEb` | 2 | `F1, F2` |
| `recvsZGkFO03l6` | 3 | `F3` |
| `recvsZGkFOVVrE` | 4 | `F4` |
| `recvsZGkFOMppC` | 5 | `F5` |
| `recvsZGkFOXori` | 6 | `F6-F9,\nFA, FC`（**硬换行**，按裁决） |
| `recvsZGkFOXPFe` | 7 | `FF` |

收窄（`Model`: `ALL` → `JE-1000F, JE-1000H, JE-1500D, JE-2000D, JE-2000E, JE-2000F, JHP-1000A, JHP-3600C`）。
回读确认 11 条**文本一字未动**，只有 `Model` 变了。回滚：改回 `ALL`。

`recvkCEhroTn5V` (F0) · `recvkCEhro1KXI` (F1) · `recvkCEhroosYR` (F2) · `recvkCEhroKfUF` (F3) ·
`recvkCEhroAiIn` (F4) · `recvkCEhroj35L` (F5) · `recvkCEhroxxbH` (F6) · `recvkCEhro5WTQ` (F7) ·
`recvkCEhroT4as` (F8) · `recvkCEhroFmNJ` (F9) · `recvkCEhroe1SA` (FE)

落笔前已核：线上 Document_key 主数据的 US/pt-BR 目标共 10 个，去掉 `JBP-2000B` 正好是上面八个，
**无遗漏无多余**——所以那条「镜像可能少目标导致主机构建硬失败」的风险已排除。

### 7.5 同步与验证

`sync-data` 后：`symbols_blocks` 17 行(内容变)、`lcd_icons` 27 → 29 行、
`troubleshooting` 45 → 52 行；`model_capabilities` 31 行未变（这次设了表 id，未重演第一批那次清空）。

`build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US`：

- `validate_spec_master` **OK**
- 三张 csv_page 表**全部通过**——`symbols page has no matching rows` 已消失
- 构建推进到下一个依赖并停在：**`AssetRegistryError: asset page/cover is not registered for model JBP-2000B`**

### 7.6 下一个阻塞点：封面资产（需要真实美术文件）

`page/cover` 是**按型号的整页 PDF**，`data/asset_registry.csv` 里只注册了
`JE-1000F` / `US` 一条。它是 BP manifest 里**唯一**的 `asset:` 引用（cover 槽，
blueprint 中 `requirement: required`），所以不能靠数据绕过。

加电包需要自己的封面 PDF。这不是入库能解决的，需要美术文件。
模板里另外三张插图（加电包正面图、左侧视图、堆叠间距图）已用 `TODO(资产)` 标注，
不会硬失败，但同样需要 `.ai` 母版。
