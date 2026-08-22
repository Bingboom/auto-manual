# JBP-2000B_US 第二批入库单：三张 csv_page 源表（待操作者确认）

日期：2026-08-22 · 目标：`JBP-2000B_US` · 前置：第一批已入库（见
[record_id 台账](jbp2000b_us_intake_record_ids_2026-08.md)），`validate_spec_master` 已 OK

来源唯一：出货书 `Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf`。
本单**不含任何已执行的写入**。

推导方式：三路独立提取（每张表一路，互不可见）+ 一路独立交叉核对。交叉核对**重新从
PDF 坐标推导**（`get_text('dict')` span 坐标 + `get_drawings()` 表格线），不用文本抽取顺序。

**核对结论：所提的值全部字节正确。** 三张表的转录（40 个值）与配对全部 CLEAN，
包括最高风险项——故障码与处置措施的配对。发现 4 处错误，**全在理由而非值上**，已在下文更正。

---

## 0. 一个必须先做的前置（三张表共用）

**`Model` 多选字段没有 `JBP-2000B` 这个选项**，三张表都是。选项不存在的写入会被直接拒绝。

| 表 | Model 字段 id | 现有选项 |
| --- | --- | --- |
| Symbols | `fld3OoJRQc` | JE-1000F / JE-2000E / JE-2000F / JE-1500D / JE-1800B / JE-900B / JE-1000H / JE-1000J / JE-300E（+1 个空名垃圾选项） |
| LCD icons | `fldjINVVwM` | 同上九项 |
| TROUBLESHOOTING | — | `Model` 是**纯文本**，无此限制 |

加选项要用 `base +field-update` 做**整份 options 数组的 PUT**，且必须带上现有选项的
`hue`/`lightness`，否则会被清掉（见 `lark-cli-bitable-ops` 的字段类型陷阱表）。
这是三处 schema 级写入，同样要你批。

写的字面量是**裸 `JBP-2000B`**（不带 `_US`）：`config.bp-us.yaml` 的 `default_model` 就是裸值，
且 `canonicalize_model_token` 在 region=US 时会剥掉尾部 `_US`/`-US`。

---

## 1. `03_内容源_Symbols`（`tblSZX8hBzpJLqAe`）— 11 条**编辑**，0 条新建

策略：**只加 Model 列，不动任何文本**。

### 1.1 先纠正一个误判

构建报错是 `symbols page has no matching rows sku= lang=en`，那个 **`sku=` 是红鲱鱼**。
`sku` 对**所有**按 `--model` 选目标的构建都是空的——包括今天能正常出书的 JE-1000F/US
（`builder.py:343-346` 的 `vars_map` 从不设 `sku_id`）。而且空 `sku` 会让
`_scope_allows` 变得**更宽松**（`renderers_common.py:126-127`），所以它不可能是不匹配的原因。

真实原因：12 条 `table_row` 全都写了明确的九主机 `Model` 列表，于是
`_matches_symbols_target`（`renderers_symbols.py:243-256`）走 Model 分支并返回 False。
`Market` 不是问题——需要的 11 行都已含 `US`。

**所以：给 Model 列表加上 `JBP-2000B` 就够了，不需要任何东西提供 sku。**
这条已在 scratchpad 里端到端实跑验证（只读，未动仓库与线上表）：改前抛出报错，
改后 en/fr/es 三语都返回左栏 6 项 + 右栏 5 项，与印刷版式逐字一致。

### 1.2 待编辑的 11 行

每行只改 `Model`，追加 `JBP-2000B`（多选是整体替换，写时要带完整新列表）。

| # | record_id | symbol_key | 文本是否需要动 |
| --: | --- | --- | --- |
| 1 | `rec277z0GFV6DG` | `warning_triangle` | **有分叉，见 §1.3** |
| 2 | `rec277z0GFV6T6` | `read_manual` | 不动（与出货书一致） |
| 3 | `rec277z0GFV738` | `electric_shock` | 不动 |
| 4 | `rec277z0GFV7aQ` | `battery_charging` | 不动 |
| 5 | `rec277z0GFV7ii` | `explosive_material` | 不动 |
| 6 | `rec277z0GFV7pR` | `heavy_object` | 不动 |
| 7 | `rec277z0GFV7wT` | `do_not_dismantle` | 不动 |
| 8 | `rec277z0GFV7Ej` | `no_open_flame` | **有分叉，见 §1.3** |
| 9 | `rec277z0GFV7LR` | `keep_away_from_children` | 不动 |
| 10 | `rec277z0GFV7Te` | `li_ion` | 不动 |
| 11 | `rec277z0GFV80p` | `weee` | 不动 |

`weee2`（order 12，`rec277z0GFV87J`）**故意不动**：出货书没印它，且渲染器对 region=US
无条件跳过它（`renderers_symbols.py:618`）。widen 它今天是空操作，但将来会静默开始印。

### 1.3 两处文本分叉——要你拍板

库里存的文本与出货书印的不同。**默认建议：保留库里现有文本，不改。** 理由是这两条都是
通用符号释义、不含主机专有行为，对加电包同样成立。

| | 出货书印的 | 库里存的 |
| --- | --- | --- |
| **#1 `warning_triangle`** EN | Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks. | Warning and Caution Symbols. Alerts individuals to information that must be read to avoid potential hazards or risks. |
| FR | Mlise en garde! Le non-respect des messages d'avertissement peut entraîner des blessures.（**印刷错字 "Mlise"**） | Symboles d'avertissement et de mise en garde. Signalent aux personnes… |
| ES | Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones. | Símbolos de advertencia y precaución. Alertan a las personas… |
| **#8 `no_open_flame`** FR | Ne pas fumer ni utiliser de flamme nue | Tenir le produit à l'écart du feu. |
| ES | No fumar ni hacer llamas abiertas | Mantenga el producto alejado del fuego. |

> **交叉核对更正 E1（重要）**：初版理由说 #8 的图标里画的是「火焰 + 香烟」，因此出货书的
> 「不要吸烟」措辞比库里的更贴合图。**这是错的。** 18 倍放大后确认那个物体是**火柴**
> （左下圆形火柴头 + 右上渐细杆），即 ISO 7010 P003 标准的「火焰+火柴」图标。
> 就图论图，库里的「远离火源」系列至少与出货书的「禁止吸烟」同样贴合。
> 分叉本身是真的，但**不要拿"图上画的是香烟"当保留出货书措辞的理由**。

若你决定改用出货书措辞：**不要同时 widen 主机行又新建 BP 行**——
`_has_unique_explicit_orders`（`renderers_symbols.py:146`）会因 order 重复直接中止。
正确做法是把该主机行的 Model 列表保持原样、另建一条同 `symbol_key` 的 BP 专属行并给它独立 order。

### 1.4 附带发现（不在本表范围）

`Localized_Copy` 里有**四**个信号块/表头单元与出货书印的略有不同（初版说三个，交叉核对补了第四个）：
FR 的 TIP 标签、以及 `symbols.header_meaning` 的 `text_es`——出货书在 printed 17 上
**三处都印复数 "Significados"**。这些不阻塞构建，记为语言资产账。

---

## 2. `03_内容源_LCD icons`（`tblW5fCuJ6YdAcND`）— 2 条**新建**

匹配只看 `Model` 列，且是**失败开放**（空值或含 `all` 即匹配全部）；`sku_id` 在
`renderers_lcd_icons.py:591` 被显式 `del` 掉。当前显式匹配 `JBP-2000B` 的行数为 0。

主机有 27 行，加电包出货书只印 **2 行**，且文字不同，故新建而非 widen。

| 字段 | 行 1 | 行 2 |
| --- | --- | --- |
| `No.` | 1 | 2 |
| `Model` | `JBP-2000B` | `JBP-2000B` |
| `Is_latest` / `Version` | TRUE / V1.0 | TRUE / V1.0 |
| `icon_en` | Power Percentage/Fault Code | Charging Indicator |
| `icon_desc_en` | The display shows the current power percentage.⏎When the system fails, it will be displayed as the corresponding fault code F0-FF. | The indicator is displayed when charging and disappears when it is fully charged. |
| `icon_fr` | Pourcentage de puissance/code d'erreur | Témoin de charge |
| `icon_desc_fr` | L'affichage de la puissance représente le pourcentage… **（含 FF 专门说明，见下）** | Le témoin s'affiche pendant la charge et disparaît lorsque l'appareil est complètement chargé. |
| `icon_es` | Porcentaje de potencia/Código de fallo | Indicador de carga |
| `icon_desc_es` | La potencia muestra el porcentaje… **（同含 FF 说明）** | Durante la carga se muestra el indicador y desaparece cuando está completamente cargado. |
| 其余七语言列 | 留空 | 留空 |
| `figure` | 留空 | 留空 |

### 待你拍板的三件

1. **出货书自己前后不一致**（最值得看的一条）：加电包的 FR/ES 故障码说明多了一句 EN 没有的
   FF 处置指引——FR「Si le code FF s'affiche, retirez la charge et le dispositif peut se
   rétablir de lui-même…」。是照抄出货书（三语不对称），还是给 EN 补上？
2. **ES 印刷错字**：`atención al cliente de Jackery.En caso de que aparezca`——句号后缺空格。
   我按出货书原样转录。是照抄还是改成 `Jackery. En caso`？
3. **`No.` 会印成带圈数字**（`components_lcd.tex:84-96` 的 `\HBCircledNum`），
   而出货书那张表**根本没有编号列**。我填了 1/2 是「最不坏」的选择，与印刷顺序一致。

另：出货书那张 LCD 表**没有任何图标图形**（该页零位图，全矢量），`figure` 留空会走
`\HBImagePlaceholder`。以及本表**没有 Region 列**，所以将来任何 `JBP-2000B_*` 区域目标
都会继承这两行（含美规书的 FR/ES 措辞）——确认是否可接受。

---

## 3. `03_内容源_TROUBLESHOOTING`（`tblOmJoAfU35brkb`）— 7 条新建 + **11 条主机行收窄**

这张表最需要你的判断，因为它要**改主机行**。

### 3.1 为什么必须改主机行

`Model=ALL` 在 `renderers_troubleshooting.py:111` 直接短路匹配，**没有「型号专有行优先于 ALL 行」的优先级**。
实跑确认：当前 `JBP-2000B/US` 会解析出 **11 条主机行**（F0,F1,F2,F3,F4,F5,F6,F7,F8,F9,FE）。
所以只加 7 条 BP 行不够——加电包页面会同时印出主机的 11 条。

**唯一的纯数据解法**是把那 11 条主机行的 `Model` 从 `ALL` 改成明确的主机清单：
`JE-1000F, JE-1000H, JE-1500D, JE-2000D, JE-2000E, JE-2000F, JHP-1000A, JHP-3600C`。

这 11 行被 8 个主机型号、US 与 pt-BR 两个区域共用。实跑验证过：改完之后
`JBP-2000B/US` 正好 7 行（三语），而 `JE-1000F/US`、`JE-1000F/pt-BR`、`JE-1500D/pt-BR`、
`JE-1000F/EU`、`JE-2000E/KR` 全部与改前**逐字一致**。

**替代方案（改代码不改数据）**：让 `_collect_rows` 认识到「存在显式命名本目标的行时，
ALL 行对该目标失效」。那样 11 条主机行一动不动。但这是渲染器改动、影响面跨所有目标，
不在数据提案范围——需要你选路线。

风险点：我那份主机清单是从 `data/model_capabilities.csv` 的 US/pt-BR doc key 推的。
**若线上构建表里有该镜像没有的 US 或 pt-BR 行，它下次构建会硬失败**（"troubleshooting page has no matching rows"）。
落地前要对着线上构建表核一遍。

### 3.2 7 条新建（`Model=JBP-2000B`、`Region=US`、`Is_latest=TRUE`、`Version=V1.0`）

配对是从表格线坐标重推的，不是按抽取顺序——EN 页的故障码和处置措施在文本抽取里是两块分开的，
按顺序配对必错。交叉核对独立重推后确认配对**三语全部正确**。

| No. | error_code | EN | FR | ES |
| --: | --- | --- | --- | --- |
| 1 | `F0` | Restart the product. | Redémarrez le produit. | Reiniciar el producto. |
| 2 | `F1, F2` | Contact Jackery Customer Support. | Contacter le service à la clientèle de Jackery. | Contacte con atención al cliente de Jackery. |
| 3 | `F3` | Restart the product. | Redémarrez le produit. | Reiniciar el producto. |
| 4 | `F4` | Connect the product to loads to discharge its battery until the fault disappears. | Connectez le produit à des charges pour décharger sa batterie jusqu'à ce que l'erreur disparaisse. | Conecte el producto a cargas para descargar su batería hasta que la falla desaparezca. |
| 5 | `F5` | Charge the product via solar panels or AC wall outlet until the fault disappears. | Chargez le produit via des panneaux solaires ou une prise murale CA jusqu'à ce que l'erreur disparaisse. | Cargue el producto mediante paneles solares o toma de corriente CA hasta que la falla desaparezca. |
| 6 | `F6-F9, FA, FC` | Contact Jackery Customer Support. | Contacter le service à la clientèle de Jackery. | Contacte con atención al cliente de Jackery. |
| 7 | `FF` | Place the product in an environment with a proper temperature and wait till the fault disappears. | Placez le produit dans un environnement à température appropriée et attendez que l'erreur disparaisse. | Coloque el producto en un ambiente con temperatura adecuada y espere hasta que la falla desaparezca. |

`FF` 是**全表新码**，现有 45 行里没有。

### 3.3 三条被交叉核对更正的理由

> **E2**：初版说「加电包没有通风间距规格，主机 F6 留着会把主机行为印进加电包书」。
> **后半句是错的**——出货书 printed 04 明确印了「Leave at least 0.66 ft (≈200 mm) of space
> between the vents and any objects」，与主机 F6 第 2 步的 0.66 ft 是同一个数字，只差单位写法
> （≈200 mm vs 20 cm）。**收窄 F6 的结论仍然成立**，但正确理由是：加电包对 F6 印的只是
> 「Contact Jackery Customer Support.」。

> **E3**：F5 说「经太阳能板或 AC 墙插充电」，而 F6/F7 的收窄理由说加电包既没 AC 输入也没太阳能 DC 输入
> ——读者会不知道该信哪个。**澄清一句**：加电包的 AC/太阳能充电**全部经由 HomePower 2000 Plus**
> （printed 06：「When charging from the wall, this product must be used with Jackery HomePower 2000 Plus」）。
> 所以出货书 F5 的措辞成立，而主机 F7 的「最大 DC 输入 60V」不成立
> （加电包的 DC 扩容输入是 36.8V–57.6V）。

> **E4**：我引的「出货书原文」里，`flamme`/`Signification` 等词在 PDF 里是**连字**
> （U+FB02 `ﬂ`、U+FB01 `ﬁ`）。这是字体连字的抽取产物不是内容差异，写进源表要规范成
> `fl`/`fi`——但标了"逐字"的引文应当说明这一点。

### 3.4 其余待定

- **`F6-F9, FA, FC` 存一行还是两行？** 印刷单元格在 `F6-F9,` 后换行，但码列只有约 41pt 宽
  （表 x 28.4–69.9），两段拼起来需要约 49pt——所以这是**软换行**，我按单行值提。
  若是硬换行，值应为 `F6-F9,\nFA, FC`。
- **`render_preview_en`** 没有任何渲染器读它（只出现在两个 schema 清单里），主机行上早已过期
  （`recvkCEhroFmNJ` 的 preview 写 "USB ports"，EN 字段却是 "DC/USB ports"）。我按 `<码>: <EN>` 填。
- **`corrective_measures_ko = "test"`** 是 11 条美规主机行上的垃圾值（CN/JP 组也有）。
  真正的韩语只在 EU/AU/KR 组。BP 新行我留空没抄这个占位值——但这笔垃圾该不该清，你定。
- **模板侧不匹配（不在本表）**：加电包会用
  `docs/templates/page_shared/{en,fr,es}/10_troubleshooting.rst`，其表头与引导句是硬编码的，
  与出货书印的略有差异。属模板账，另计。
- `data/source_table_contracts/phase2_source_tables.json:449` 记录的
  `reference_table_id` 是 `tblUSuk3Q5BKTdTh`，在本 base 里 **not_found**；实际表是 `tblOmJoAfU35brkb`。
  只报告，未动。

---

## 4. 汇总与执行顺序

| 步骤 | 操作 | 数量 |
| --: | --- | --- |
| 0 | 三张表的 `Model` 多选加 `JBP-2000B` 选项（Symbols/LCD 各一次；TROUBLESHOOTING 无需） | 2 处 schema 写入 |
| 1 | Symbols：11 条 `Model` 列表编辑 | 11 编辑 |
| 2 | LCD icons：2 条新建 | 2 新建 |
| 3 | TROUBLESHOOTING：7 条新建 | 7 新建 |
| 4 | TROUBLESHOOTING：11 条主机行 `ALL` → 明确清单（**需单独授权**） | 11 编辑 |
| 5 | 每次写入后逐条回读，报 record_id + 字段 | — |
| 6 | `build.py sync-data`（**务必设 `FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID`**，否则会把能力镜像清成表头） | — |
| 7 | `build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US` | — |

第 7 步当前基线：`validate_spec_master` 已 OK，构建停在
`symbols page has no matching rows`。本单三张表落地后该错应消失。

回滚：新建行逐条可删（record_id 会记录）；编辑类改回原值，原值已在本单列出。

## 5. 需要你回答的问题清单

1. §1.3 两处符号文本分叉：保留库里现有文本（默认建议），还是改用出货书措辞？
2. §2 加电包 FR/ES 多出的 FF 说明：照抄出货书的三语不对称，还是给 EN 补齐？
3. §2 ES 印刷错字 `Jackery.En caso`：照抄还是修正？
4. §3.1 **是否授权改那 11 条主机共用行**？还是走改渲染器的替代方案？
5. §3.4 `F6-F9, FA, FC` 单行还是硬换行？
