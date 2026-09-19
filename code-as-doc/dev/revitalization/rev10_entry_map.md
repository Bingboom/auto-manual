# REV-10 · M4 稳定入口映射表 v1

- 版本：**v1**（首版立表）；生成（UTC）：2026-09-19T03:36Z
- 数据时点：Hello-Docs `main` tip **b8c09fd9a953f2dd386e912507c5e478fbdb2b6f**（2026-09-17T10:51:09Z；publish_manifest built_at 2026-09-17T07:23:17Z）；auto-manual `origin/main` = **58767931ba8f8b5d35fff2a725febce8fba66c28**
- 表结构约定：每行一个稳定入口；「历史变更记录」栏本期为空（立表结构）——今后每次入口指向变化在该栏追加 `日期 | 旧目标 → 新目标 | 依据(PR/HD#)`，不覆盖旧行。
- 语义规则（方案 §5.2-3）：本表只登记「最新版稳定入口」；绑定历史版本的链接（发布目录 alidocs 行、旧站冻结快照）**不入本表**，保留版本语义，见 rev02_link_audit.csv。
- 入口生成机制（读码证据见 rev02_conclusions.md §2）：根别名 = `tools/readthedocs_source.py::_write_short_aliases`（按 manual stem 自动派生）+ `tools/rtd_alias_entry.py`（noindex+canonical+延迟跳转，beacon 可计数）；legacy 兼容页 = `publish_meta.json` 的 `legacy_default/legacy_aliases/legacy_route` → `tools/publish_branch_assembly.py::_write_legacy_compatibility_routes`。

站点基址：`https://ht-doc.readthedocs.io`（单版本、根路径直出）。

## 0. 门户入口

| 稳定入口 | 文档身份 | 当前目标 | 内容版本 | 历史变更记录 |
| --- | --- | --- | --- | --- |
| `/`（Manual Center 门户） | portal-index | 门户列 52 手册链接 | n/a | （空） |

## 1. 根别名（印刷/QR 可计数入口层，52 个 = 全部发布目标）

自动跟随发布目标存在，**登记状态列为派生事实**：目标撤下则别名随下一次装配消失（如 HD#89 撤下的 JE-5000A_JP / JHP-3600A_US 两别名已不在）。

| 稳定入口（根别名） | 文档身份 | 当前目标（嵌套正式路由） | 内容版本（写入时点） | 历史变更记录 |
| --- | --- | --- | --- | --- |
| `/manual_jaad01a_eu_en.html` | JA-AD01A-EU-en | `/JA-AD01A/EU/en/md/manual_jaad01a_eu_en.html` | git-20260906-0252cb5d | （空） |
| `/manual_jaad600a_eu_en.html` | JA-AD600A-EU-en | `/JA-AD600A/EU/en/md/manual_jaad600a_eu_en.html` | 2.0 | （空） |
| `/manual_jaca05b_eu_en.html` | JA-CA05B-EU-en | `/JA-CA05B/EU/en/md/manual_jaca05b_eu_en.html` | git-20260909-f5359ac0 | （空） |
| `/manual_jaca3sa_eu_en.html` | JA-CA3SA-EU-en | `/JA-CA3SA/EU/en/md/manual_jaca3sa_eu_en.html` | git-20260909-88f1fa0d | （空） |
| `/manual_jacc30a_eu_en.html` | JA-CC30A-EU-en | `/JA-CC30A/EU/en/md/manual_jacc30a_eu_en.html` | git-0eb2b7ba | （空） |
| `/manual_jaacwhe100eua1_eu_en.html` | JAAC-WHE-100-EUA1-EU-en | `/JAAC-WHE-100-EUA1/EU/en/md/manual_jaacwhe100eua1_eu_en.html` | candidate | （空） |
| `/manual_jbp2000b_eu_de.html` | JBP-2000B-EU-de | `/JBP-2000B/EU/de/md/manual_jbp2000b_eu_de.html` | 2.0 | （空） |
| `/manual_jbp2000b_eu.html` | JBP-2000B-EU-en | `/JBP-2000B/EU/en/md/manual_jbp2000b_eu.html` | 2.0-20260913 | （空） |
| `/manual_jbp2000b_eu_es.html` | JBP-2000B-EU-es | `/JBP-2000B/EU/es/md/manual_jbp2000b_eu_es.html` | 2.0 | （空） |
| `/manual_jbp2000b_eu_fr.html` | JBP-2000B-EU-fr | `/JBP-2000B/EU/fr/md/manual_jbp2000b_eu_fr.html` | 2.0 | （空） |
| `/manual_jbp2000b_eu_it.html` | JBP-2000B-EU-it | `/JBP-2000B/EU/it/md/manual_jbp2000b_eu_it.html` | 2.0 | （空） |
| `/manual_jbp3600a_eu.html` | JBP-3600A-EU-en | `/JBP-3600A/EU/en/md/manual_jbp3600a_eu.html` | 2.0 | （空） |
| `/manual_je1000f_eu_de.html` | JE-1000F-EU-de | `/JE-1000F/EU/de/md/manual_je1000f_eu_de.html` | 2.0 | （空） |
| `/manual_je1000f_eu_en.html` | JE-1000F-EU-en | `/JE-1000F/EU/en/md/manual_je1000f_eu_en.html` | 2.0 | （空） |
| `/manual_je1000f_eu_es.html` | JE-1000F-EU-es | `/JE-1000F/EU/es/md/manual_je1000f_eu_es.html` | 2.0 | （空） |
| `/manual_je1000f_eu_fr.html` | JE-1000F-EU-fr | `/JE-1000F/EU/fr/md/manual_je1000f_eu_fr.html` | 2.0 | （空） |
| `/manual_je1000f_eu_it.html` | JE-1000F-EU-it | `/JE-1000F/EU/it/md/manual_je1000f_eu_it.html` | 2.0 | （空） |
| `/manual_je1000f_us.html` | JE-1000F-US-en | `/JE-1000F/US/en/md/manual_je1000f_us.html` | 2.3 | （空） |
| `/manual_je1000h_eu_de.html` | JE-1000H-EU-de | `/JE-1000H/EU/de/md/manual_je1000h_eu_de.html` | 2.0 | （空） |
| `/manual_je1000h_eu_en.html` | JE-1000H-EU-en | `/JE-1000H/EU/en/md/manual_je1000h_eu_en.html` | 2.0 | （空） |
| `/manual_je1000h_eu_es.html` | JE-1000H-EU-es | `/JE-1000H/EU/es/md/manual_je1000h_eu_es.html` | 2.0 | （空） |
| `/manual_je1000h_eu_fr.html` | JE-1000H-EU-fr | `/JE-1000H/EU/fr/md/manual_je1000h_eu_fr.html` | 2.0 | （空） |
| `/manual_je1000h_eu_it.html` | JE-1000H-EU-it | `/JE-1000H/EU/it/md/manual_je1000h_eu_it.html` | 2.0 | （空） |
| `/manual_je1000h_eu_uk.html` | JE-1000H-EU-uk | `/JE-1000H/EU/uk/md/manual_je1000h_eu_uk.html` | 2.0 | （空） |
| `/manual_je100c_eu_en.html` | JE-100C-EU-en | `/JE-100C/EU/en/md/manual_je100c_eu_en.html` | 2.0 | （空） |
| `/manual_je2000e_eu_de.html` | JE-2000E-EU-de | `/JE-2000E/EU/de/md/manual_je2000e_eu_de.html` | 2.0 | （空） |
| `/manual_je2000e_eu_en.html` | JE-2000E-EU-en | `/JE-2000E/EU/en/md/manual_je2000e_eu_en.html` | 2.0-20260913 | （空） |
| `/manual_je2000e_eu_es.html` | JE-2000E-EU-es | `/JE-2000E/EU/es/md/manual_je2000e_eu_es.html` | 2.0 | （空） |
| `/manual_je2000e_eu_fr.html` | JE-2000E-EU-fr | `/JE-2000E/EU/fr/md/manual_je2000e_eu_fr.html` | 2.0 | （空） |
| `/manual_je2000e_eu_it.html` | JE-2000E-EU-it | `/JE-2000E/EU/it/md/manual_je2000e_eu_it.html` | 2.0 | （空） |
| `/manual_je2000e_eu_uk.html` | JE-2000E-EU-uk | `/JE-2000E/EU/uk/md/manual_je2000e_eu_uk.html` | 2.0 | （空） |
| `/manual_je2000f_eu_de.html` | JE-2000F-EU-de | `/JE-2000F/EU/de/md/manual_je2000f_eu_de.html` | 2.0 | （空） |
| `/manual_je2000f_eu_en.html` | JE-2000F-EU-en | `/JE-2000F/EU/en/md/manual_je2000f_eu_en.html` | 2.0-20260913 | （空） |
| `/manual_je2000f_eu_es.html` | JE-2000F-EU-es | `/JE-2000F/EU/es/md/manual_je2000f_eu_es.html` | 2.0 | （空） |
| `/manual_je2000f_eu_fr.html` | JE-2000F-EU-fr | `/JE-2000F/EU/fr/md/manual_je2000f_eu_fr.html` | 2.0 | （空） |
| `/manual_je2000f_eu_it.html` | JE-2000F-EU-it | `/JE-2000F/EU/it/md/manual_je2000f_eu_it.html` | 2.0 | （空） |
| `/manual_je2000f_eu_uk.html` | JE-2000F-EU-uk | `/JE-2000F/EU/uk/md/manual_je2000f_eu_uk.html` | 2.0 | （空） |
| `/manual_je3000c_eu_de.html` | JE-3000C-EU-de | `/JE-3000C/EU/de/md/manual_je3000c_eu_de.html` | 2.0 | （空） |
| `/manual_je3000c_eu_en.html` | JE-3000C-EU-en | `/JE-3000C/EU/en/md/manual_je3000c_eu_en.html` | 2.0-20260913 | （空） |
| `/manual_je3000c_eu_es.html` | JE-3000C-EU-es | `/JE-3000C/EU/es/md/manual_je3000c_eu_es.html` | 2.0 | （空） |
| `/manual_je3000c_eu_fr.html` | JE-3000C-EU-fr | `/JE-3000C/EU/fr/md/manual_je3000c_eu_fr.html` | 2.0 | （空） |
| `/manual_je3000c_eu_it.html` | JE-3000C-EU-it | `/JE-3000C/EU/it/md/manual_je3000c_eu_it.html` | 2.0 | （空） |
| `/manual_je3000c_eu_uk.html` | JE-3000C-EU-uk | `/JE-3000C/EU/uk/md/manual_je3000c_eu_uk.html` | 2.0 | （空） |
| `/manual_je300d_eu_en.html` | JE-300D-EU-en | `/JE-300D/EU/en/md/manual_je300d_eu_en.html` | candidate-2025-10-24 | （空） |
| `/manual_je3600a_eu_en.html` | JE-3600A-EU-en | `/JE-3600A/EU/en/md/manual_je3600a_eu_en.html` | 2026-05-25 | （空） |
| `/manual_je3600a_eu_es.html` | JE-3600A-EU-es | `/JE-3600A/EU/es/md/manual_je3600a_eu_es.html` | 2026-05-25 | （空） |
| `/manual_je3600a_eu_fr.html` | JE-3600A-EU-fr | `/JE-3600A/EU/fr/md/manual_je3600a_eu_fr.html` | 2026-05-25 | （空） |
| `/manual_je500a_eu_en.html` | JE-500A-EU-en | `/JE-500A/EU/en/md/manual_je500a_eu_en.html` | 2.0-20260913 | （空） |
| `/manual_js100f_eu_en.html` | JS-100F-EU-en | `/JS-100F/EU/en/md/manual_js100f_eu_en.html` | 1.0 | （空） |
| `/manual_js100i_eu_en.html` | JS-100I-EU-en | `/JS-100I/EU/en/md/manual_js100i_eu_en.html` | 2.0 | （空） |
| `/manual_js200e_eu_en.html` | JS-200E-EU-en | `/JS-200E/EU/en/md/manual_js200e_eu_en.html` | 2.0 | （空） |
| `/manual_js40c_eu_en.html` | JS-40C-EU-en | `/JS-40C/EU/en/md/manual_js40c_eu_en.html` | 2026-08-30 | （空） |

## 2. legacy_route 兼容入口（22 个 legacy_default 目标）

旧「无语言段」路径形态的兼容跳转页（`<MODEL>/<REGION>/md/`），目标 = 该本书默认语言（legacy_default=true）的正式路由。`legacy_aliases` 当前全部等于各自 manual stem，无自定义附加名。

| 稳定入口（兼容页） | 文档身份 | 当前目标（嵌套正式路由） | 内容版本（写入时点） | 历史变更记录 |
| --- | --- | --- | --- | --- |
| `/JA-AD01A/EU/md/index.html` + `/JA-AD01A/EU/md/manual_jaad01a_eu_en.html` | JA-AD01A-EU-en | `/JA-AD01A/EU/en/md/manual_jaad01a_eu_en.html` | git-20260906-0252cb5d | （空） |
| `/JA-AD600A/EU/md/index.html` + `/JA-AD600A/EU/md/manual_jaad600a_eu_en.html` | JA-AD600A-EU-en | `/JA-AD600A/EU/en/md/manual_jaad600a_eu_en.html` | 2.0 | （空） |
| `/JA-CA05B/EU/md/index.html` + `/JA-CA05B/EU/md/manual_jaca05b_eu_en.html` | JA-CA05B-EU-en | `/JA-CA05B/EU/en/md/manual_jaca05b_eu_en.html` | git-20260909-f5359ac0 | （空） |
| `/JA-CA3SA/EU/md/index.html` + `/JA-CA3SA/EU/md/manual_jaca3sa_eu_en.html` | JA-CA3SA-EU-en | `/JA-CA3SA/EU/en/md/manual_jaca3sa_eu_en.html` | git-20260909-88f1fa0d | （空） |
| `/JA-CC30A/EU/md/index.html` + `/JA-CC30A/EU/md/manual_jacc30a_eu_en.html` | JA-CC30A-EU-en | `/JA-CC30A/EU/en/md/manual_jacc30a_eu_en.html` | git-0eb2b7ba | （空） |
| `/JAAC-WHE-100-EUA1/EU/md/index.html` + `/JAAC-WHE-100-EUA1/EU/md/manual_jaacwhe100eua1_eu_en.html` | JAAC-WHE-100-EUA1-EU-en | `/JAAC-WHE-100-EUA1/EU/en/md/manual_jaacwhe100eua1_eu_en.html` | candidate | （空） |
| `/JBP-2000B/EU/md/index.html` + `/JBP-2000B/EU/md/manual_jbp2000b_eu.html` | JBP-2000B-EU-en | `/JBP-2000B/EU/en/md/manual_jbp2000b_eu.html` | 2.0-20260913 | （空） |
| `/JBP-3600A/EU/md/index.html` + `/JBP-3600A/EU/md/manual_jbp3600a_eu.html` | JBP-3600A-EU-en | `/JBP-3600A/EU/en/md/manual_jbp3600a_eu.html` | 2.0 | （空） |
| `/JE-1000F/EU/md/index.html` + `/JE-1000F/EU/md/manual_je1000f_eu_en.html` | JE-1000F-EU-en | `/JE-1000F/EU/en/md/manual_je1000f_eu_en.html` | 2.0 | （空） |
| `/JE-1000F/US/md/index.html` + `/JE-1000F/US/md/manual_je1000f_us.html` | JE-1000F-US-en | `/JE-1000F/US/en/md/manual_je1000f_us.html` | 2.3 | （空） |
| `/JE-1000H/EU/md/index.html` + `/JE-1000H/EU/md/manual_je1000h_eu_en.html` | JE-1000H-EU-en | `/JE-1000H/EU/en/md/manual_je1000h_eu_en.html` | 2.0 | （空） |
| `/JE-100C/EU/md/index.html` + `/JE-100C/EU/md/manual_je100c_eu_en.html` | JE-100C-EU-en | `/JE-100C/EU/en/md/manual_je100c_eu_en.html` | 2.0 | （空） |
| `/JE-2000E/EU/md/index.html` + `/JE-2000E/EU/md/manual_je2000e_eu_en.html` | JE-2000E-EU-en | `/JE-2000E/EU/en/md/manual_je2000e_eu_en.html` | 2.0-20260913 | （空） |
| `/JE-2000F/EU/md/index.html` + `/JE-2000F/EU/md/manual_je2000f_eu_en.html` | JE-2000F-EU-en | `/JE-2000F/EU/en/md/manual_je2000f_eu_en.html` | 2.0-20260913 | （空） |
| `/JE-3000C/EU/md/index.html` + `/JE-3000C/EU/md/manual_je3000c_eu_en.html` | JE-3000C-EU-en | `/JE-3000C/EU/en/md/manual_je3000c_eu_en.html` | 2.0-20260913 | （空） |
| `/JE-300D/EU/md/index.html` + `/JE-300D/EU/md/manual_je300d_eu_en.html` | JE-300D-EU-en | `/JE-300D/EU/en/md/manual_je300d_eu_en.html` | candidate-2025-10-24 | （空） |
| `/JE-3600A/EU/md/index.html` + `/JE-3600A/EU/md/manual_je3600a_eu_en.html` | JE-3600A-EU-en | `/JE-3600A/EU/en/md/manual_je3600a_eu_en.html` | 2026-05-25 | （空） |
| `/JE-500A/EU/md/index.html` + `/JE-500A/EU/md/manual_je500a_eu_en.html` | JE-500A-EU-en | `/JE-500A/EU/en/md/manual_je500a_eu_en.html` | 2.0-20260913 | （空） |
| `/JS-100F/EU/md/index.html` + `/JS-100F/EU/md/manual_js100f_eu_en.html` | JS-100F-EU-en | `/JS-100F/EU/en/md/manual_js100f_eu_en.html` | 1.0 | （空） |
| `/JS-100I/EU/md/index.html` + `/JS-100I/EU/md/manual_js100i_eu_en.html` | JS-100I-EU-en | `/JS-100I/EU/en/md/manual_js100i_eu_en.html` | 2.0 | （空） |
| `/JS-200E/EU/md/index.html` + `/JS-200E/EU/md/manual_js200e_eu_en.html` | JS-200E-EU-en | `/JS-200E/EU/en/md/manual_js200e_eu_en.html` | 2.0 | （空） |
| `/JS-40C/EU/md/index.html` + `/JS-40C/EU/md/manual_js40c_eu_en.html` | JS-40C-EU-en | `/JS-40C/EU/en/md/manual_js40c_eu_en.html` | 2026-08-30 | （空） |

## 3. 跨站映射（旧站 → 新站）

直接引用 REV-01 产出：`../rev01/rev01_url_map.csv`（53 行 = 门户 1 + 52 目标；两站重叠目标只有 JE-1000F-US-en，旧 1.7 → 新 2.3；其余 51 个新站独有）。要点：

| 旧站入口（ht-manuals.readthedocs.io） | 新站对应 | 本轮实测（2026-09-19T03:31Z） |
| --- | --- | --- |
| `/en/latest/JE-1000F/US/md/manual_je1000f_us.html` | 同路径换域名 → 新站 200 兼容跳转页 → `/JE-1000F/US/en/md/manual_je1000f_us.html` | 旧 200（冻结快照仍在线）/ 新 200 |
| `/`（旧 furo index） | `/`（Manual Center 门户） | 旧 200 / 新 200 |

## 4. 登记外入口（本表不管理，仅备注）

- 构建表 HTML_link 3 条非空值（2 嵌套 + 1 平铺，形态不一致待 M2/M4 统一，见 rev02_conclusions.md §1）。
- 发布目录 45 条 alidocs 链接：历史版本绑定语义，永不改指向，不属稳定入口。
- 印刷 QR：现有 3 个已登记印刷 QR 均为物料号非 URL——**当前没有任何印刷物绑定 RTD 入口**，故「保护已印二维码」暂无实际保护对象（rev02_conclusions.md §2）。
