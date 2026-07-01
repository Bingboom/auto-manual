---
name: new-region-line
description: Stand up a NEW region / compliance manual line end-to-end (e.g. 新建韩规/欧规/日规安规产线, "add a KR line", "onboard a new market", "新增一个区域/语言产线", "新建安规产线要补什么配置和料"). Covers everything from zero: the config + manifest + templates, the code registration for a new output language, the Feishu source-table data entry (spec params, page placeholders, localized content, market tags), sync, and validation — plus the checklist of inputs the operator must supply (spec-sheet PDF, product name, warranty/legal, compliance & translation decisions). Use when creating a line that does not exist yet. NOT for editing an existing line's data (that is normal spec ingest / rewrite / backport).
---

# New Region / Compliance Manual Line

Bring up a brand-new market line — a `(Model, Region, Language)` target — so
`build.py check` passes and the manual can build. This is the generalized
playbook proven on the **KR (韩规) JE-1000F ko** line.

A line spans **four surfaces**, and skipping any one leaves the build broken:

1. **Repo config/templates** — a family config, a manifest, cloned page templates.
2. **Repo code** — register the output language everywhere langs are enumerated.
3. **Feishu source tables** — spec params, page placeholders, localized content,
   plus market/region tags and dictionary/master entries.
4. **Operator inputs** — the spec-sheet PDF, product display name, legal/warranty
   values, and the compliance + translation decisions only a human can make.

Read [`references/setup-map.md`](references/setup-map.md) for the exact files,
table IDs, `lark-cli` recipes, and command sequence. Keep it open while you work.

## ⚠️ Land repo changes in `auto-manual`, NOT the `Hello-Docs` mirror

`Bingboom/Hello-Docs` is a **one-way, destructive mirror** of `Bingboom/auto-manual`:
`.github/workflows/sync-hello-docs.yml` runs on every push to **auto-manual/main** and
`rsync -a --delete`s auto-manual's tree onto Hello-Docs/main. **Any repo change
committed only in Hello-Docs is wiped on the next sync** — a PR into Hello-Docs is
the wrong target.

So for surfaces 1 & 2 (config/manifest/templates/code/`data/phase2/page_registry.csv`):
- Make the changes in **`auto-manual`** and PR into **`auto-manual/main`**; the mirror
  picks them up automatically after merge.
- **Before committing, run `git remote -v` and confirm you are in `auto-manual`**, not
  Hello-Docs. On this machine auto-manual is a sibling: `../auto-manual`.
- If you only have a Hello-Docs checkout, port via an **isolated worktree** so you don't
  disturb any in-progress branch:
  `git -C ../auto-manual fetch origin && git -C ../auto-manual worktree add -b <branch> <path> origin/main`
  (apply changes there → validate → PR into auto-manual/main).

Surfaces 3 & 4 (Feishu source tables + operator inputs) are **shared** and unaffected
by which git repo — they live in Feishu, not the tree.

## When to use

- The `(Model, Region)` or output language does **not** exist yet in the repo.
- Trigger phrases: "新建韩规/欧规产线", "add a new region line", "onboard a new
  market/language", "新建安规产线需要补什么配置/什么料".

Do **not** use for: editing an existing line's spec values (that is plain spec
ingest via the 入库表), translating/rewriting copy (`manual-rewrite-with-tm`),
or back-porting reviewed docs (`manual-revision-backport`).

## Inputs the operator MUST supply (什么料)

The build cannot be completed without these — collect them up front:

| Input | Why | Notes |
|---|---|---|
| **规格书 PDF** (model+region) | source of every spec parameter | e.g. `HTE…-KR-JAK 规格书.pdf`; watch the **version** (A0 vs A1) |
| **Region code + regime** | region slug + certs | e.g. `KR`/韩规-KC, `EU`/欧规-CE, `AU`/澳规-RCM |
| **Source lang + output lang(s)** | config `languages`, code registration | e.g. source EN → monolingual `ko` |
| **Product display name** | cover/title; **not in the spec PDF** (cover is an image) | e.g. `Jackery Explorer 1000` — must be confirmed |
| **Warranty email + legal company** | `rst_substitutions` | e.g. `hello.kr@jackery.com`, `Jackery` |
| **`word_title`** in target language | Word output title | e.g. `|PRODUCT_NAME| 사용자 매뉴얼` |
| **Compliance decisions** | which safety **symbols** (Market tag) and **certs** apply; which **error codes** | KC vs CE vs RCM sets differ — a compliance call, not a guess |
| **Translations** for localized content | symbols text, LCD icon desc, troubleshooting, signal words | can start as **placeholder** (`test` / English fallback) and be filled later |

If any are missing, surface them and stop rather than inventing values — the
product name, warranty email, and compliance/symbol sets are the common gaps.

## Workflow (high level — details in references/setup-map.md)

1. **Branch** off up-to-date **`auto-manual/main`** (NOT the Hello-Docs mirror — see
   the ⚠️ section above; confirm `git remote -v`). Use `scripts/start_branch.sh`, or a
   worktree if porting from a Hello-Docs checkout.
2. **Config + templates**: clone an existing line (pick the closest regime).
   Copy its `config.*.yaml` (keep the **full `paths` block**), `manifest`, and
   `page_*` template dirs; set region/lang/substitutions.
3. **Register the language in code** (only if the output lang is new): see the
   registration checklist in `setup-map.md` (`signal_words.py`,
   `sync_data_models.py`, `localized_copy.py`, `manual_copy_source.py`,
   `page_registry.csv`).
4. **Feishu data**: create the `document_key` + region dictionary entries;
   enter spec params (via the 入库表 + 字段映射规则表 → operator confirms → source
   table) and page placeholders; add the language columns + content + KR/region
   market tags to symbols/lcd/troubleshooting; ensure the TM has the language.
5. **Sync**: `build.py sync-data` (full run for TM-derived files).
6. **Validate**: `build.py check` for the new target, plus a **regression check**
   on an existing region, plus `python -m unittest`.
7. **PR into `auto-manual/main`** per AGENTS.md §8.6 (never into the Hello-Docs mirror).

## Validation (must pass before PR)

```
python build.py check --config configs/config.<region>.yaml --model <MODEL> --region <REGION>
python build.py check --config configs/config.us.yaml --model JE-1000F --region US   # regression
python -m unittest
python tools/check_maintainability_guardrails.py
```

If you changed hardcoded schema/expectations, update the matching tests
(`tests/test_sync_data.py`, `tests/test_manual_copy_source.py`).

## Related skills / references

- Spec extraction + intake: this repo's 入库表 + 字段映射规则表 flow (see setup-map).
- Translations: `bitable-translation-memory`, `manual-rewrite-with-tm`.
- Reverse-sync of reviewed docs: `manual-revision-backport`.
- Full data-architecture reference: [`references/setup-map.md`](references/setup-map.md).
