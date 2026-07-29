# Working-set coordinates

The authoritative, full table-level inventory of the business-plane bases is
[`user-guide/two_plane_map.md`](../../../../user-guide/two_plane_map.md) §1.1
(operator-enumerated) — consult it for anything not listed here, and treat it
as the tiebreaker when this working set drifts. This file keeps only the ids
used week-to-week, so a session doesn't re-derive them.

## 文档构建 base (business plane, tenant xcn57j1urbe6)

- BASE_TOKEN = `LD3lb4G1ua4GOVs1vxAc9W2enje` (the base/app_token) — wiki node `BLYEwfMMFiS7wsk9MuvcOvdVnje`

| Table | table_id | Notes |
| --- | --- | --- |
| 入库暂存表 (spec-intake staging) | `tblIi0BEufjvGLIU` | `状态` options ✅直通/🔧已变换/⚠️需确认 = engine direct/transformed/needs_review; close batches via 入库结果 |
| 规格书字段映射规则 (rule library) | `tblHrelfzylJIRT2` | generic template — the real sibling's structure wins on divergence |
| 内容源_规格参数明细 (specs source) | `tblPUFJqt2uGGvTT` | KR/JP/CN rows carry `Value_<lang>`/`Row_label_<lang>` beside `Value_source` — they move together |
| 内容源_页面占位参数 (placeholders) | `tblEhqJVXiyKtnwq` | |
| 主数据_Document_key | `tbltnkDIdwiDOP7d` | document_key/项目代码 are formulas — write the Model/Region links |
| 主数据_区域法规 (regions) | `tblvBsr8qGPjXWdA` | |
| 内容源_Symbols | `tblSZX8hBzpJLqAe` | `Model` multi-select shared rows; `Market` select |
| 内容源_LCD icons | `tblW5fCuJ6YdAcND` | `Model` multi-select; no region dimension |
| 内容源_TROUBLESHOOTING | `tblOmJoAfU35brkb` | `Region` is TEXT (comma-shared, e.g. `EU, AU`) |
| 规格页Footnotes | `tblVusBZ8Fi56AWN` | shared `Model` multi-select + scalar `Footnote_order` — per-model renumbering means SPLITTING the record |
| 内容源_插图资产表 (asset registry) | `tblxFBWaDG4OYhqu` | `.ai` masters + per-asset attachments live here |
| 文档构建 (build/queue table, document_link) | `tblbnRHjpJeCVTtj` | InReview rows, `Git_ref`, 「基线文档」frozen baseline, `是否触发文档构建` Y/已构建 |

- 过程文档管理 (baseline/review cloud-doc home): wiki node
  `AvBhwdpNxivgXfkPm1VcCG01nPh` (child of the 文档构建 node) — baseline
  re-snapshots (`wiki +node-copy`) land here with dated titles.

## Translation_Memory (canonical write base = "B"/env base)

- BASE_TOKEN = `Ji1hb5ub1aUbewsTljGccvx5nhc`
  (wiki node `FRUywcjrPiMoPrkxnadcQhhenmb`, tenant xcn57j1urbe6)
- 句对表 `tblqtvNbgjDwR4ya` (view `veweqW2fQv`) · 术语表 `tblzerRpOEuDIkKA`
  (view `vewChPXyP9`)
- The old wiki "A" base is read-only archive — never write it.

## Model identity convention

- `document_key` always uses the **canonical** model + region
  (`JE-1000F_AU`); marketing/manufacturer names (`HTE1531000A-AU-JAK`,
  `Jackery Explorer 1000`) go into the `Model No.` / product-name **values**
  only.
