---
name: product-manual-catalog
description: Look up shipped product manuals and catalog overview from the Feishu "发布文档管理" Base. Use for chat asks like "JE-2000F 的说明书"、"日规有哪些说明书"、"产品总览"、"给我某产品的用户手册链接", i.e. finding a product's manual link, version, region, or document type, and for summarizing what manuals exist. This is a read-only catalog lookup, distinct from the phase2 build-source tables and from Translation_Memory.
---

# Product Manual Catalog

Use this skill when the user wants to **find or summarize shipped product manuals** — the manual link, version, region, document type, lifecycle stage, or a catalog overview. The source is the Feishu **「发布文档管理」** Base (a published-manual catalog), which is separate from the phase2 build-source tables and from `Translation_Memory`.

Do **not** use this skill to build, review, or publish a manual (that is the queue/build flow), and do not use it for sentence translation (that is `bitable-translation-memory`).

## What the catalog holds

One row per published manual, keyed informally by 产品型号 + 区域 + 文档类型 + 版本. Key fields: `产品型号`, `产品简称`, `产品名称_en/jp/zh/kr`, `区域`, `文档类型`, `源语言`, `版本`, `产品阶段`, `分类`, `归档日期`, `Is_latest`, owners (`产品经理`/`项目经理`/`系统工程师`/`设计`/`资料开发`), and the canonical `说明书链接` (a DingTalk alidocs link).

## Default workflow

Run the query script in the foreground and wait for the one result. It reads with the **bot** identity (record reads require it) and resolves the Base token from the stable wiki node at runtime.

- Find a product's manual(s):
  `python3 .agents/skills/product-manual-catalog/scripts/query_product_manuals.py "JE-2000F"`
- Catalog overview (counts by 分类 / 区域 / 产品阶段 / 文档类型 / 源语言):
  `python3 .agents/skills/product-manual-catalog/scripts/query_product_manuals.py --overview`
- Narrow with filters (combine freely):
  `--region 日规` · `--doc-type "User Manual"` · `--stage PVT` · `--category 便携储能-主机` · `--latest-only`
- List everything (subject to filters): `--list`
- Structured output for further processing: `--format json`

Results are sorted latest-version-first, so the freshest manual is the default answer.

## Output rules

- Render each `说明书链接` as a Markdown link with the manual name as anchor text — e.g. `[Jackery Explorer 2000 User Manual V2.0](https://alidocs.dingtalk.com/i/nodes/…)` — so Feishu shows it as a clickable document card. Never paste a bare URL. The script already formats links this way; keep that form when you relay the answer.
- When several manuals match one model (different regions/languages/colors), list them as separate bulleted links rather than picking one silently; if the user named a region or language, filter to it first.
- For a single clear lookup, answer with the matched manual(s) directly; do not narrate "我先查表" unless the user asks how you found it.
- Prefer `Is_latest = True` rows; mention non-latest versions only if the user asks for history or there is no latest row.
- For an overview ask, return the summary as-is; do not dump every row unless the user asks to list them.

## Bindings

Defaults point at the live table (wiki node `QKNGwHFwPiY7J7kZ0bzcximKnyb`, table `tbldqnNBxFQsxpeN`, view `vewytqcvDc`). Override per call with `--wiki-token` / `--table-id` / `--view-id` / `--base-token`, or via env `FEISHU_PUBLISHED_DOCS_WIKI_TOKEN` / `_TABLE_ID` / `_VIEW_ID` / `_BASE_TOKEN`. A Base copy that keeps the same wiki node needs no code change.
