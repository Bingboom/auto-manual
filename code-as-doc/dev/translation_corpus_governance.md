# Translation Corpus Governance (句对库 + 术语库)

Updated: 2026-06-01

This is the operating contract for the two CAT tables that live in the Feishu Base
「多维表CAT」: the sentence-pair **Translation Memory (句对库)** and the
**Glossary / termbase (术语库)**. It defines who owns which string, how to maintain
both without keeping two divergent sources, and how to audit drift.

It is a sibling of [`external_table_contracts.md`](external_table_contracts.md): that file
governs the phase2 build/queue tables; this file governs the translation-reference corpus.
The two overlap in exactly one place — **status words** (see §6).

Operational tooling lives in:

- [`bitable-translation-memory`](../../.agents/skills/bitable-translation-memory/SKILL.md) — read/lookup layer
- [`bilingual-tm-maintenance`](../../.agents/skills/bilingual-tm-maintenance/SKILL.md) — evidence-first write/maintenance layer
- [`query_live_translation_memory.py`](../../.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py) — live sentence-pair query

---

## 1. Table identity

| | Translation Memory (句对库) | Glossary (术语库) |
| --- | --- | --- |
| Role | full source→target **sentences/segments** for reuse and leverage | controlled **terms / UI labels / status words**, one canonical target each |
| Base token | `LUIcbxeKdaCY2rsEHwCcnVQSnUe` | `LUIcbxeKdaCY2rsEHwCcnVQSnUe` |
| Wiki node | `X3O8wCpXPifqGKkP2sYccyxznQb` | `X3O8wCpXPifqGKkP2sYccyxznQb` |
| Table id | `tbl6gKPJPTvOcTWv` | `tblBIEtLSoAA6W9U` |
| Default view | `veweqW2fQv` (all langs); `vewjFtFSBk` = en/kr slice | `vewChPXyP9` |

If the base token stops resolving, re-derive it from the wiki node:
`lark-cli wiki spaces get_node --params '{"token":"X3O8wCpXPifqGKkP2sYccyxznQb"}'` → `data.node.obj_token`.

---

## 2. Single-source principle (the core rule)

The goal is **not** to merge the two tables — TM and termbase are two layers of a CAT
system and serve different jobs. The goal is: **every string has exactly one authoritative
translation, stored once, in its home table.** The other table *references* it; it never
re-stores a second copy.

Four rules follow:

1. **Granularity decides the home table.**
   - A **term** — a UI label, component name, mode name, or status word, in practice ≤ 4 source words — lives in the **glossary only**.
   - A **sentence/segment** lives in the **TM only**.
   - The boundary is machine-detectable today: glossary `en` is 1–4 words (median 2); TM `en` median is 8 words. There is no overlap band.

2. **One authoritative translation per (string, language).** It is written in the home table only. The other table must not carry a hand-typed second copy.

3. **One row per source string.** Model is a **tag on that single row**, never a reason to duplicate the row. Duplicating a sentence per model is what produces same-source-different-target drift (already observed — see §8).

4. **Cross-references go through the link/lookup bridge, not copy-paste.** See §4.

---

## 3. Language-column standard — standardized 2026-06-01

Both tables now use **identical** language column names:
`en` `zh` `fr` `es` `de` `it` `uk` `jp` `ko` `pt-BR`.

| Language | Column | Was (句对库 / 术语库) → now |
| --- | --- | --- |
| Korean | `ko` | `kr` / `ko-KR` → unified to **`ko`** |
| Ukrainian | `uk` | `uk` / `乌克兰语` → unified to **`uk`** |
| Japanese | `jp` | `jp` / `jp` → **kept `jp`** |
| Others | `en` `zh` `fr` `es` `de` `it` `pt-BR` | already consistent |

**Japanese stays `jp`, not BCP-47 `ja`** — the phase2 build convention uses `jp` throughout
(`label_jp`, `troubleshooting_jp`, `STATUS_WORD_COLUMNS` in
[`manual_copy_source.py`](../../tools/manual_copy_source.py)), so the CAT tables match the build
rather than diverging. Korean and Ukrainian are **not** phase2 build columns (only `en zh jp
fr es pt-BR de it uk` feed `Status_Words.csv`), so unifying them was build-safe.

Renaming a language column is a **contract change**: update both tables and the recognized field
set in
[`query_live_translation_memory.py`](../../.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py)
(now includes `ko`) in the same change. The `term_<lang>` lookups reference glossary columns by
**field ID**, so a rename does not break them.

---

## 4. The term ↔ sentence bridge

> Concrete landing plan (relation field, all-language lookups, the 46-term migration with
> record IDs): [`translation_corpus_bridge_plan.md`](translation_corpus_bridge_plan.md).

A seed of the right design already exists but is half-built:

- TM field `筛选术语值` is a lookup `from "Terms"` (the glossary) — but it only mirrors the
  glossary `fr` column and covers ~33/839 rows.
- Glossary field `筛选` is a lookup `from "Translation_Memory"` — but it only mirrors the TM
  `it` column and covers ~42/98 rows.

Target design:

- Keep a **relation field** linking a TM sentence to the glossary term(s) it contains.
- The glossary stays the **single authority** for term translations. Term-level QA
  (does this sentence use the approved target term?) reads the glossary through the link.
- Do **not** copy a term's translations into TM cells. A short string that is genuinely a
  term should not also exist as its own TM row — it lives in the glossary and is referenced.
- The ~46 short strings currently present in **both** tables are the redundancy to retire:
  keep them in the glossary, drop them from the TM (or convert to a reference).

---

## 5. Maintenance SOP (录入纪律)

Before adding or editing any pair:

1. **Classify** term vs sentence (§2.1). Pick the home table.
2. **Search both tables** for the source `en` first. Reuse beats re-entry.
3. **Update the existing `en`-linked row** rather than creating a duplicate — this is already
   the documented rule in
   [`bilingual-tm-maintenance`](../../.agents/skills/bilingual-tm-maintenance/SKILL.md);
   it is the discipline that prevents per-model duplication.
4. **Write the target only in the home table.** Never type a term's translation into both
   tables.
5. **Never duplicate a sentence per model.** Add the model as a tag on the one row.
6. **Normalize on write**: trim leading/trailing whitespace, collapse double spaces, strip
   stray leading newlines.
7. **Append, don't overwrite** the per-language 维护Log / 校验Log, per the skill's log rules.
8. **Verify the write** with `record-get` or projected JSON — never trust CLI echo for
   non-ASCII (skill rule).

Conflict handling: if the same `en` already has a *different* target in the other table,
do not silently pick one. Record it as a cross-table conflict (§8) and let the owner (夏冰)
choose the authoritative value.

---

## 6. Status-word contract (shared boundary with the build)

"Status word" here means the **LCD state words `On` / `Off` / `Blink`** — not the safety
signal words. Do not conflate the two:

- **LCD status words (`On`/`Off`/`Blink`)** carry `是否为 status word=Y`. Per
  [`external_table_contracts.md`](external_table_contracts.md) §1, those flagged TM rows sync
  to `Status_Words.csv`, which [`renderers_lcd_icons.py`](../../tools/csv_pages/renderers_lcd_icons.py)
  reads to **bold the prefix** of LCD icon descriptions ("**On:** Bluetooth connected"). The
  snapshot is currently **complete**: exactly 3 rows (On/Off/Blink) are flagged.
- **Safety signal words (`WARNING`/`CAUTION`/`DANGER`/`NOTE`)** are a *different* category —
  section headings, not LCD states. They are **not** flagged `是否为 status word`, and must
  not be, or they would wrongly enter the LCD bolding snapshot.

Rules:

- `On`/`Off`/`Blink` are terms whose canonical target belongs in the glossary, **but they are
  also the live source of `Status_Words.csv`**. Before the bridge migration deletes their TM
  rows (§4 / [`translation_corpus_bridge_plan.md`](translation_corpus_bridge_plan.md)), either
  keep those 3 rows in the TM (flagged) as the snapshot source, or repoint the sync to build
  `Status_Words.csv` from the glossary.
- `Blink` `pt-BR` differs across tables (glossary `Pisca` vs TM `Piscando`); `Status_Words.csv`
  currently ships the TM value `Piscando`, so resolving that conflict changes build output.

---

## 7. Drift rules / change discipline

- A language-column rename, addition, or removal updates **both tables**, this document, and
  the live-query language mapping in the same change. Prefer aliases before removals (§3).
- The term↔sentence relation is a contract: changing what the bridge surfaces, or its
  direction, updates this document and any consumer.
- Schema/coverage audits run against pulled snapshots, not assumptions — re-run the audit in
  §8 before asserting the corpus is clean.
- External column names (including the Chinese log/flag columns) are product contracts.

---

## 8. Health metrics & periodic audit

Re-runnable audit dimensions (pull both tables via
`lark-cli base +record-list --base-token <bt> --table-id <tid> --format json`, paginate on
`--offset` until `has_more=false`, align row values to `.data.fields`):

1. **Source integrity** — rows with empty `en`, or `en` containing no letter of any script (bare numbers, callout circled-numbers, stray punctuation) = noise with zero TM value.
2. **Duplicate `en`** — within each table; for TM, whether duplicates are per-model copies and whether their targets agree.
3. **Cross-table overlap & conflict** — `en` present in both tables, and where both targets are filled but differ.
4. **Coverage** — fill rate per language column.
5. **Text hygiene** — leading/trailing/double whitespace, leading newlines; real encoding corruption (`�`, UTF-8-as-Latin1 digraphs) vs legitimate diacritics.
6. **Status-word coverage** — `是否为 status word=Y` count vs the status words actually present (§6).
7. **Bridge coverage** — how many rows have a populated term↔sentence link.

### Baseline — 2026-06-01 audit

Translation Memory (`tbl6gKPJPTvOcTWv`): **839 rows**, 798 distinct `en`.

| Lang | en | es | fr | de | it | pt-BR | kr | uk | jp | zh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Filled | 100% | 71% | 71% | 62% | 61% | 41% | 37% | 18% | 8% | 6% |

Glossary (`tblBIEtLSoAA6W9U`): **98 rows**, 83 distinct `en` (15 are empty shadow duplicates).

| Lang | en | pt-BR | zh | fr | es | de | it | uk | jp | ko-KR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Filled | 100% | 69% | 58% | 55% | 55% | 39% | 39% | 39% | 39% | 2% |

> This is the pre-cleanup baseline. The 2026-06-01 Phase 1 harvest
> ([`translation_corpus_bridge_plan.md`](translation_corpus_bridge_plan.md)) has since raised
> glossary coverage (e.g. `ko-KR` 2% → 39%, `pt-BR` 69% → 83%).

Open items found:

- TM: 1 empty-source row (`recvlfSn0Qmb17`, since gone); per-model duplicate sentences **merged 2026-06-01** — 22 truly-redundant groups collapsed (31 rows removed, `Model` multi-select union, `Glossary_term` links preserved). Of the 6 genuinely-divergent groups, **4 resolved 2026-06-01** (merged to the chosen value with per-language maintenance/audit logs — incl. replacing an untranslated DE placeholder + fixing its typo), **2 kept separate as legitimately distinct** (`bypass-mode` model-specific wording; `CHARGING` heading-vs-status). Whitespace **normalized 2026-06-01** (27 TM + 8 GL cells, internal newlines preserved). Numeric/symbol noise rows **removed 2026-06-01** — 24 TM rows whose `en` had no letter of any script (15 bare numbers `9`–`24`, 8 callout circled numbers `①`–`⑧`, 1 stray fragment `60%).`), each translated to itself = zero TM value. TM now **737 rows**. Resolution detail + backups: `~/corpus_divergence_pending_2026-06-01.md`, `~/tm_divergence_resolve_backup_2026-06-01.json`, `~/tm_numeric_junk_backup_2026-06-01.json`.
- Glossary: 15 duplicate-`en` rows (twins carrying only `en`+`pt-BR`) — **merged + deleted 2026-06-01** (unique `pt-BR` harvested into the full row first; 98 → 83 rows, duplicate `en` now 0).
  `No` filled on only 31/98 with repeated values (not a key).
- Cross-table: 46 `en` strings in both tables; 4 confirmed target conflicts (`fr` danger=DANGER/ATTENTION, `fr` ups=UPS (ASI)/ASI, `pt-BR` blink=Pisca/Piscando, `it` ac wall charging indicator=…a parete/…da muro).
- Status words: 3/839 flagged = `On`/`Off`/`Blink` (the complete LCD snapshot, → `Status_Words.csv`); safety words `WARNING`/`DANGER`/`CAUTION` are correctly not flagged.
- No real encoding corruption (0 `�`, 0 UTF-8-as-Latin1 digraphs); earlier Portuguese "mojibake" flags were false positives on legitimate `Ã`/`Ç`.

Cleanup of the live base (deleting shadow rows, merging per-model duplicates, reconciling
conflicts, normalizing whitespace) is a **separate, owner-approved step** — it mutates the
source of truth and must be proposed as a dry-run before any write.
