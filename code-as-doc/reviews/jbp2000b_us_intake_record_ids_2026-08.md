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

symbols 报错里 `sku=` 为空，说明加电包目标未解析出 sku——补数据时要一并确认匹配是走 `Model` 还是 sku。
