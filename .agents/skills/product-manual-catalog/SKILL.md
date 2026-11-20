---
name: product-manual-catalog
description: Look up shipped product manuals and catalog overview from the Feishu "发布文档管理" Base. Use for chat asks like "JE-2000F 的说明书"、"日规有哪些说明书"、"产品总览"、"给我某产品的用户手册链接", i.e. finding a product's manual link, version, region, or document type, and for summarizing what manuals exist. This is a read-only catalog lookup, distinct from the phase2 build-source tables and from Translation_Memory.
---

# Product Manual Catalog

Use this skill when the user wants to **find or summarize shipped product manuals** — the manual link, version, region, document type, lifecycle stage, or a catalog overview. The source is the Feishu **「发布文档管理」** Base (a published-manual catalog), which is separate from the phase2 build-source tables and from `Translation_Memory`.

Do **not** use this skill to build, review, or publish a manual (that is the queue/build flow), and do not use it for sentence translation (that is `bitable-translation-memory`).

## What the catalog holds & bot table-permission fallback

- **Primary master table (`tbldqnNBxFQsxpeN` / `vewytqcvDc`)**: when accessible (for example under `--identity user` or when bot table permission is enabled), holds `产品型号`, `产品简称`, `产品名称_en/jp/zh/kr`, `区域`, `文档类型`, `源语言`, `版本`, `产品阶段`, `分类`, `归档日期`, `Is_latest`, owners, and `说明书链接`.
- **Table-permission trap under `--identity bot`**: in `发布文档管理` (`WGVwb2HctauRi7sEiKqcIzTRn1c`), `tbldqnNBxFQsxpeN` is currently not exposed to the enterprise `bot` identity (Feishu returns `1254004 WrongTableId` / `800030104 not_found`). Never treat that as "the base is empty" — and do **not** assume `--identity user` is available headless.
- **Automatic bot-accessible fallback**: when `tbldqnNBxFQsxpeN` returns a table-access/not-found error and no explicit `--table-id` / `FEISHU_PUBLISHED_DOCS_TABLE_ID` override was passed, `query_product_manuals.py` automatically falls back to the bot-accessible **`网页文档` (`tblY0i9JUElmuuKb`)** table (`型号`, `商品简称`, `项目号`, `客户型号(关联)`, `规格型号`, `适用产品`, `市场`, `文档类型`, `语言`, `产品类别`, `产品系列`, `容量档`, and published RTD `超链接`). If a non-overview query finds 0 rows in `网页文档`, it checks **`说明书转网页` (`tbljbjaXaTD6V9PO`)** as a secondary fallback for unconverted print-source manuals. Pass `--no-fallback` to fail closed.

## Default workflow

Run the query script in the foreground and wait for the one result. It reads with the **bot** identity (stable for headless/OpenClaw runs) and resolves the Base token from the stable wiki node at runtime.

- Find a product's manual(s):
  `python3 .agents/skills/product-manual-catalog/scripts/query_product_manuals.py "JE-2000F"`
- Catalog overview (counts by 分类 / 区域 / 产品阶段 / 文档类型 / 源语言):
  `python3 .agents/skills/product-manual-catalog/scripts/query_product_manuals.py --overview`
- Narrow with filters (combine freely):
  `--region 日规` (aliases `日规`/`JP`, `美加规`/`US`, `欧英规`/`EU` match both forms) · `--doc-type 产品说明书` · `--stage PVT` · `--category 便携储能` · `--latest-only`
- List everything (subject to filters): `--list`
- Structured output for further processing: `--format json`

Results are sorted latest-version-first, so the freshest manual is the default answer.

## Query rules — search one code, filter the rest

- Put **only a single 型号 or 项目 code** in the search argument (e.g. `HTE153`, `JE-2000F`). 项目 codes such as `HTE153` are searchable — the catalog matches them in the `项目` field.
- **Never put a region / 文档类型 / 版本 inside the search string.** The match is substring-per-field, so `"HTE139 欧规"` matches nothing and returns 0 rows. Apply those as `--region` / `--doc-type` filters, or filter the returned rows after a bare-code search.
- A "型号/项目 + 区域" ask like "HTE139 欧规的说明书" means: search `HTE139` (or add `--region 欧规`), then keep the 欧规 row(s) — **not** search the literal string "HTE139 欧规".
- If a code search returns 0 rows, retry with just the bare code (or a looser code) before telling the user 查不到.

## Output rules

- Render each `说明书链接` as a Markdown link with the manual name as anchor text — e.g. `[Jackery Explorer 2000 User Manual V2.0](https://alidocs.dingtalk.com/i/nodes/…)` or `[JE-2000F (美加规 · 英语)](https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/...)` — so Feishu shows it as a clickable document card. Never paste a bare URL. The script already formats links this way; keep that form when you relay the answer.
- When several manuals match one model (different regions/languages/colors), list them as separate bulleted links rather than picking one silently; if the user named a region or language, filter to it first.
- For a single clear lookup, answer with the matched manual(s) directly; do not narrate "我先查表" unless the user asks how you found it.
- Prefer `Is_latest = True` rows; mention non-latest versions only if the user asks for history or there is no latest row.
- For an overview ask, return the summary as-is; do not dump every row unless the user asks to list them.

## Bindings

Defaults point at the live table (wiki node `QKNGwHFwPiY7J7kZ0bzcximKnyb`, primary table `tbldqnNBxFQsxpeN`, view `vewytqcvDc`, bot-accessible web catalog fallback `tblY0i9JUElmuuKb` / secondary print-source fallback `tbljbjaXaTD6V9PO`). Override per call with `--wiki-token` / `--table-id` / `--view-id` / `--base-token`, or via env `FEISHU_PUBLISHED_DOCS_WIKI_TOKEN` / `_TABLE_ID` / `_VIEW_ID` / `_BASE_TOKEN`. A Base copy that keeps the same wiki node needs no code change.
