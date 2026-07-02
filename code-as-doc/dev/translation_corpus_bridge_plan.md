# Translation Corpus Bridge — Landing Plan

Updated: 2026-06-01
Status: **Phases 1–3 + cleanup complete** (2026-06-01) — single-source migration, the
`Glossary_term` relation, 182 sentence→term links, all 9 `term_<lang>` lookups, per-model
sentence merge, whitespace + glossary-dedup, and language-column standardization
(`ko`/`uk`, `jp` kept) are all live and verified. Every write step was owner-approved (夏冰).

> **Phase 1 done (2026-06-01):** harvested 112 translations from TM term-rows into empty
> glossary cells across 42 records (verified 112/112; conflict cells untouched). Glossary
> coverage: `ko-KR` 2→38, `pt-BR` 68→81, `fr`/`es` 54→66, `de`/`it` 38→50, `zh` 57→62,
> `uk`/`jp` 38→43. Relation field `Glossary_term` (`fldUeZQZTZ`, one-way) created on the TM
> table → glossary.
>
> **Phase 2 done (2026-06-01):** conflicts resolved (`danger`/`ups`/`ac wall` kept the
> glossary value; `blink` pt-BR set to `Piscando`); `On`/`Off`/`Blink` kept in the TM as the
> `Status_Words.csv` source (flagged); **45 duplicate term-rows deleted** from the TM (backup:
> `~/tm_termrows_backup_2026-06-01.json`); both legacy lookups (`筛选术语值`, `筛选`) dropped.
> Cross-table `en` overlap is now **3** (only the On/Off/Blink status-word exceptions). TM is
> now 797 rows (45 term-rows removed; the verified gate confirmed all 45 target ids gone and
> the 3 status rows preserved).
>
> **Phase 3 done (2026-06-01):** sentence→term linking — 182 TM sentences linked to the
> multi-word glossary terms they contain (242 links, verified 182/182 written, 8/8 sample
> read-back). All **9 `term_<lang>` lookups created** (term_fr via the Feishu UI, the other 8
> via `lark-cli` — both work; §3) and verified link-following (Bluetooth row → "Bluetooth" /
> "블루투스", single linked-term value, not a whole-table rollup). They surface each linked
> term's approved target per language for QA. Short/ambiguous single-word terms
> (on/off/note/handle…) were intentionally **not** auto-linked; link them by hand as needed.

This is the concrete execution plan for §4 of
[`translation_corpus_governance.md`](translation_corpus_governance.md): build one clean
term↔sentence bridge, turn the single-language lookup into all-language lookups, and retire
the 46 short strings that are duplicated across both tables.

---

## 0. Ground truth (verified 2026-06-01)

> **G4 base convergence (2026-07-02):** the coordinates below describe the
> **A/wiki mirror**, which is now a **read-only archive**. The canonical live
> Translation_Memory / Terms base is whatever `$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN`
> names (tables resolved by name inside it); every skill/script write path
> targets that base. Do not write the archive.

- Table names behind the IDs: TM `tbl6gKPJPTvOcTWv` is named **`Translation_Memory`**;
  glossary `tblBIEtLSoAA6W9U` is named **`Terms`**. The legacy lookups' `from` values
  (`"Terms"` / `"Translation_Memory"`) are these **table names**, not relation-field names.
- **lark-cli hides link/relation-type fields** from `+field-list`, `+table-get`, and
  `+record-list`. The legacy link exists server-side (its lookups return values for 33/839
  TM and 42/98 glossary rows) but cannot be read or reliably managed through the CLI.
  → **Verify link state through the lookups (readable) or the Feishu UI, never by reading the
  link cell via CLI.**
- **lark-cli field types are string discriminators, not the Feishu numeric codes**
  (`text` `number` `select` `datetime` `link` `formula` `lookup` `attachment` …). A
  `--dry-run` does **not** validate the payload — only the real call does. Verified by
  execution:
  - Relation field: `{"field_name":"Glossary_term","type":"link","link_table":"<tbl_id>"}`
    — flat `link_table` at the top level (NOT `property.table_id`, NOT `type:21`). Created
    one-way (`bidirectional:false`); making it two-way needs `+field-update … --yes`
    (high-risk, full-PUT).
  - Link-cell write: `+record-upsert --record-id <rid> --json '{"<link field id>":["<rec_id>"]}'`
    (verified). The link cell is **readable per-row** via `+record-get --field-id <link fld>`
    (returns `[{"id":"rec..."}]`) even though `+record-list`/`+field-list` hide link fields.
  - **Link-following lookups CAN be created via CLI** — the trick is a *field-reference* match
    condition, not a constant one. A constant condition (e.g. `en isNotEmpty`) makes a
    table-wide rollup that ignores the link; a `field_ref` condition matching the glossary key
    against the link field follows the link. Empty `where.conditions` is rejected by the API
    (only the UI's internal API allowed the legacy empty-condition lookups). See §3 for the
    exact payload.
- **`+record-batch-update` only does uniform patch** (`{record_id_list, patch}`) — it cannot
  apply different values per record. For heterogeneous writes use per-record
  `+record-upsert --record-id <rid> --json @<relative-path>` (PATCH semantics: only the given
  fields change). `@file` paths must be **relative to cwd**; absolute Windows paths are
  rejected. Localized text goes through a UTF-8 file, never inline (skill rule).
- The first write in a session may return a transient
  `check incr user_access_token scope fail` (code 2200); **retry succeeds**. The user token
  (唐夏冰) holds full `base:record:*` / `base:field:*` scopes.

---

## 1. Target structure

```
Translation_Memory (sentence)                         Terms / glossary
  en  : "On: Bluetooth connected."                      en : "Bluetooth"
  fr  : "Activé : Bluetooth connecté."                  fr : "Bluetooth"
  Glossary_term  ─── link (type 21) ───►  (one or more) ko-KR : "블루투스"
  term_fr  (lookup → glossary.fr)   ◄── surfaced for QA  ...
  term_ko  (lookup → glossary.ko-KR)
  ...
                          ◄─── reverse auto-field "Used_in_sentences" in glossary
```

- **Glossary stays the single authority** for term targets.
- TM gets **one** relation field `Glossary_term` (type 21, two-way) plus **per-language
  lookups** `term_<lang>` that surface the glossary's canonical target for QA.
- The two legacy lookups (`筛选术语值`, `筛选`) and their hidden link are **dropped** (§6).

---

## 2. Relation field (the bridge)

Create once, on the TM table, pointing at the glossary. **Done 2026-06-01** —
`Glossary_term` = `fldUeZQZTZ`, one-way.

```powershell
lark-cli base +field-create --base-token LUIcbxeKdaCY2rsEHwCcnVQSnUe --table-id tbl6gKPJPTvOcTWv `
  --json '{"field_name":"Glossary_term","type":"link","link_table":"tblBIEtLSoAA6W9U"}'
```

The create response returns the new `fld...` id (capture it — `+table-get`/`+field-list` will
**not** list link fields afterward; CLI limitation). To make it two-way (adds a reverse
"used-in-sentences" field on the glossary), run `+field-update … --field-id fldUeZQZTZ --yes`
with `bidirectional:true` — high-risk full-PUT, currently left one-way.

---

## 3. All-language lookups — **9 created & verified 2026-06-01**

The legacy `筛选术语值` surfaced only glossary `fr`. It is replaced with one lookup per
language, each reading the glossary field through the `Glossary_term` link:

| TM lookup | glossary target column | glossary field id |
| --- | --- | --- |
| `term_zh` | zh | `fldyyHoBFy` |
| `term_fr` | fr | `fldyjUfB8U` |
| `term_es` | es | `fldPEQoGOq` |
| `term_de` | de | `fldt6BzFRt` |
| `term_it` | it | `flduItRNgY` |
| `term_pt-BR` | pt-BR | `fldKaXcnTu` |
| `term_uk` | 乌克兰语 | `fld6k2itpg` |
| `term_ja` | jp | `fld0jnHIge` |
| `term_ko` | ko-KR | `fldy9fiac8` |

### CLI recipe (verified)

The lookup follows the link when its match condition is a **field reference**, not a constant.
Match the glossary key (`en`, `fldt7ZEWwl`) against the `Glossary_term` link field
(`fldUeZQZTZ`) — the link displays each linked term's primary (`en`), so the equality resolves
to exactly the linked term(s):

```powershell
lark-cli base +field-create --base-token LUIcbxeKdaCY2rsEHwCcnVQSnUe --table-id tbl6gKPJPTvOcTWv `
  --i-have-read-guide --json '{"field_name":"term_es","type":"lookup","from":"tblBIEtLSoAA6W9U",
  "select":"fldPEQoGOq","where":{"conditions":[["fldt7ZEWwl","is",{"type":"field_ref","field":"fldUeZQZTZ"}]],"logic":"and"}}'
```

- `from` = glossary table id; `select` = the glossary language column id (table above).
- condition tuple = `["<glossary en id>","is",{"type":"field_ref","field":"<Glossary_term id>"}]`.
  `field_ref` (not `field`/`value`) is the key; a `constant` value (e.g. `isNotEmpty`) would
  roll up the whole table instead.

Equivalent in the **Feishu UI**: add field → 查找引用 → 数据表 `Terms`, 引用字段 = the column;
查找条件 `en` 等于 当前表 `Glossary_term`. (term_fr was built this way; the other 8 via the CLI.)

Verified link-following on the Bluetooth-linked row `recvgEwErzZXBk`: all 9 return the single
linked term's value (`Bluetooth` / `블루투스`), not a whole-table concatenation.

---

## 4. Migrate the 46 duplicated term-rows

The 46 strings that live in **both** tables are short terms wrongly stored as TM rows (they
map to 48 TM rows; only `energy saving mode` and `note` have a per-model duplicate). They split
into three buckets. **Value mostly flows TM → glossary**, because the TM term-rows are often
more complete than the glossary — most carry a `ko-KR` value the glossary lacks (glossary
`ko-KR` is only 2/98). Harvesting them lifts glossary `ko-KR` from 2 to ~40.

For every bucket the per-row routing is in the [appendix](#appendix-46-term-routing-table).

### Bucket A — CONFLICT (4): resolve authority first

Glossary and TM disagree on at least one language. 夏冰 picks the authoritative value, then the
row is treated as bucket B.

| en | lang | glossary | TM | note |
| --- | --- | --- | --- | --- |
| danger | fr | `DANGER` | `ATTENTION` | safety status word — reconcile first |
| ups | fr | `UPS (ASI)` | `ASI` | |
| blink | pt-BR | `Pisca` | `Piscando` | |
| ac wall charging indicator | it | `…a parete` | `…da muro` | |

### Bucket B — GLOSSARY-GAP (38): harvest up, then delete

Glossary has the term but is missing languages the TM term-row holds. For each: copy the TM
values into the empty glossary cells (`+record-batch-update` on the glossary record), verify the
write (`+record-get` projected JSON — never trust CLI echo for non-ASCII), then delete the TM
term-row.

### Bucket C — CLEAN (4): delete TM term-row

Glossary already authoritative and complete enough (`charging power limit`, `connected
batteries`, `discharge timer`, `tou mode`). Just delete the TM term-row.

### ⚠ Status-word exception (do NOT delete blindly)

The LCD status words **`On`/`Off`/`Blink`** are in this set and are the **live source of
`Status_Words.csv`** — they are the only 3 TM rows flagged `是否为 status word=Y`, and
[`renderers_lcd_icons.py`](../../tools/csv_pages/renderers_lcd_icons.py) bolds LCD description
prefixes from them. (Verified: `On recvlaG0kwW8cT`, `Off recvkCSqieddqx`,
`Blink recvlaG14WzSJN` all `=Y`.) Safety words `warning`/`caution`/`danger`/`note` are NOT
flagged and are not a build dependency.

Before deleting the On/Off/Blink TM rows:

1. Re-home the snapshot — either keep these 3 rows in the TM (flagged) as the source, or
   repoint the sync to build `Status_Words.csv` from the glossary.
2. Note `Blink` `pt-BR`: glossary `Pisca` vs TM `Piscando`; the shipped `Status_Words.csv`
   currently uses `Piscando`, so the bucket-A conflict resolution changes build output.

### Net effect

- Delete ~44–48 TM term-rows (after the status-word carve-out), removing the term/sentence
  granularity violation and the duplicate-source drift.
- Enrich the glossary with the harvested cells (biggest win: `ko-KR` 2 → ~40).
- TM is left holding **sentences only**.

---

## 5. Link the sentences

The bridge's job is linking each TM **sentence** to the glossary term(s) it contains.

**Done 2026-06-01 (multi-word terms only).** For each of the 56 multi-word glossary terms, TM
rows whose `en` contains the term as a whole phrase (`(?<!\w)term(?!\w)`, case-insensitive) were
linked via per-row `+record-upsert --json '{"fldUeZQZTZ":["<term rec_id>", ...]}'`. Result: **182
sentences, 242 links** (49 sentences carry multiple terms); written 182/182, sample read-back
8/8. Verified per-row with `+record-get --field-id fldUeZQZTZ` (the link is not visible in
`+record-list`).

**Deliberately skipped:** single-word / generic terms (`on`, `off`, `note`, `handle`,
`vehicle`, `bluetooth`, `wi-fi`, `documents`, `ups`, plus the safety words) — substring matching
on those over-links. Link them by hand, or run a higher-precision pass later. One single-word
link was made manually as the end-to-end test (`bluetooth` sentence `recvgEwErzZXBk`).

Re-running is safe: the matcher recomputes from live data; writes are additive and idempotent
per row (the link is replaced with the full matched set each time).

---

## 6. Retire legacy + standardize

- ~~Delete the legacy lookups `筛选术语值` (TM) and `筛选` (glossary)~~ **done 2026-06-01.** The
  hidden legacy link field they sat on cannot be seen or removed via lark-cli; it remains
  orphaned but harmless (nothing reads it).
- Language-column standardization **done 2026-06-01** (governance SOP §3): Korean `kr`/`ko-KR`
  → `ko`, Ukrainian `乌克兰语` → `uk` in both tables; **Japanese kept as `jp`** to match the
  phase2 build convention (changing to `ja` would diverge from `STATUS_WORD_COLUMNS` etc.).
  [`query_live_translation_memory.py`](../../.agents/skills/bitable-translation-memory/scripts/query_live_translation_memory.py)
  now recognizes `ko`. Both tables now share `en zh fr es de it uk jp ko pt-BR`.

---

## 7. Execution order & safety

1. **Export first** — dump the 48 TM term-rows (all fields) to a local JSON; deletions are
   destructive and the CLI cannot show the link cell to confirm nothing else points at them.
2. Resolve bucket A conflicts (owner decision).
3. Resolve the status-word sourcing (§4 exception).
4. Create `Glossary_term` (§2).
5. Harvest bucket B values into the glossary; verify each write.
6. Create the `term_<lang>` lookups (§3) — confirm property shape on the first one.
7. Delete bucket B + C (and A-after-resolution, and status words after re-homing) TM term-rows.
8. Drop the legacy lookups (§6).
9. Re-run the §8 audit in the governance SOP; confirm overlap → 0 and no new conflicts.
10. Begin sentence-linking waves (§5).

Every write step: `--dry-run` → inspect → execute → read back. Stop and report if any step's
dry-run payload looks wrong.

---

## Appendix: 46-term routing table

`bucket | en | glossary rec_id | TM rec_id(s) | glossary cols to harvest from TM`

```
A  ac wall charging indicator    recvgQ442MSWZ1  recvgEwErzNRle           ko-KR  (+conflict it)
A  blink  ⚠status                recvj5gianbXaJ  recvlaG14WzSJN           zh fr es de it 乌 jp ko-KR  (+conflict pt-BR)
A  danger                        recvgQMh5lcb0B  recvgEwErzm3KB           pt-BR  (+conflict fr)
A  ups                           recvgQ3YGjQEdg  recvgEwErzni7A           ko-KR  (+conflict fr)
B  ac input                      recvj5gian201w  recvgEwErz7o5Z           fr es de it ko-KR
B  ac output                     recvj5gianZnCr  recvgEwErzJ6kk           fr es de it
B  ac power button               recvj5gianY0IB  recvkfilA3VRTn           ko-KR
B  ac power indicator            recvgQ3XfYUAM3  recvgEwErzzxtZ           ko-KR
B  auto-off                      recvj5giancqJy  recvgEwErzwDiE           fr es de it ko-KR
B  battery power indicator       recvgQ49Ca7SRd  recvgEwErzN41x           pt-BR ko-KR
B  battery saving mode           recvgQ47dFIDTQ  recvgEwErzvV2m           ko-KR
B  bluetooth                     recvgWjF5048S1  recvgEwErzsKKq           ko-KR
B  car charging indicator        recvgQ45i5G9dM  recvgEwErz7duL           pt-BR ko-KR
B  caution                       recvgQMmrtpZ0C  recvkfi363S6jo           ko-KR
B  charging plan                 recvgQ3ROnE5Wc  recvgEwErz7YPw           ko-KR
B  dc/usb power button           recvj5gianjWmF  recvgEwErz5pAX           fr es de it
B  documents                     recvgEwWsoAB0a  recvkfiiztjPIn           pt-BR
B  energy saving mode            recvgQ4gyhxLZz  recvgEwErzQy57,recvgEwErzAKdk  pt-BR ko-KR  (TM x2)
B  fault code                    recvgQ4jzE3dEJ  recvgEwErz5EFK           pt-BR ko-KR
B  handle                        recvgEwWsof4ot  recvgEwErzZWPH           pt-BR
B  high temperature indicator    recvgQ4hpPpUkk  recvgEwErz5skh           pt-BR ko-KR
B  input power                   recvgQ41hFzFGZ  recvgEwErzMnEi           pt-BR ko-KR
B  low battery indicator         recvgQ4diXCON9  recvgEwErzSoVU           ko-KR
B  low temperature indicator     recvgQ4igsJazT  recvgEwErzmInd           pt-BR ko-KR
B  main power button             recvj5ghDHZqgs  recvgEwErzqy3W           fr es de it ko-KR
B  note                          recvgQMocklVYd  recvkfi40mG3mn,recvkkDWhoqns7  ko-KR  (TM x2)
B  off  ⚠status                  recvj5gianmEPA  recvkCSqieddqx           zh fr es de it 乌 jp ko-KR
B  on   ⚠status                  recvj5gianIfz7  recvlaG0kwW8cT           zh fr es de it 乌 jp ko-KR
B  output power                  recvgQ4kuZp5Ph  recvgEwErzFtGD           pt-BR ko-KR
B  output voltage and frequency  recvgQ405jBd7o  recvgEwErzJxCk           ko-KR
B  quiet charging mode           recvgEwWsouWSe  recvgEwErzqu0N           ko-KR
B  remaining battery percentage  recvgQ4aKwAOvW  recvgEwErzHf2T           pt-BR ko-KR
B  remaining charge time         recvgQ42AmZk54  recvgEwErzAtDT           ko-KR
B  remaining discharge time      recvgQ4lBpYL3y  recvgEwErzuSuI           ko-KR
B  self-powered mode             recvgEwWsotFEu  recvgEwErzpYKb           ko-KR
B  solar charging indicator      recvgQ46lJCAWu  recvgEwErzF6Ri           pt-BR ko-KR
B  turn off                      recvj5gianfwV7  recvgEwErzF3Bu           fr es de it ko-KR
B  turn on                       recvj5giannQv6  recvgEwErzUDsK           zh fr es de it 乌 jp ko-KR
B  user manual                   recvkHCIWFlLBj  recvgEwErzd0ji           zh fr es de it 乌 jp
B  vehicle                       recvj5gianJtJL  recvgEwErzpi1X           fr es de it ko-KR
B  warning                       recvgQMgAwyDVs  recvgEwBBukyXI           ko-KR
B  wi-fi                         recvgWjEhVR7Xk  recvgEwErzQnGO           ko-KR
C  charging power limit          recvgQ48tCnB1N  recvgEwErzfIcJ           —
C  connected batteries           recvgQ4fdVr8Hz  recvgEwErzPJye           —
C  discharge timer               recvgQ4e5AZhVB  recvgEwErzM8yk           —
C  tou mode                      recvgQ3VLEnCJR  recvgEwErzUgyW           —
```

(`乌` = glossary `乌克兰语`. ⚠status = status word; see §4 exception before deleting its TM row.)
