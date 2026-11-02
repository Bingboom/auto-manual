# JE-1000F EU uk/pt/nl/pl: shared symbols and the Web-only battery row

Status: active

## Request and scope (2026-11-02)

The operator asked「先用修正版.ai 把荷波葡乌的电池图标补上」. The revised AI
`JE-1000F_修正版.ai` (`30bcad90…`, 161 pages, from the `发布文档管理` record) has
seven-row symbol tables in all nine languages, ending with WEEE, and no
batteries-and-accumulators row. de/es/it got their battery row from phase2 data,
not from print, and en/fr already carry it Web-only. The operator chose
「网页版单独补（同英法）」.

In scope: the uk/pt/nl/pl symbol table of the frozen four-language package. No
other copy, image or IR block changes.

## Why every row changes

Fresh symbol admission requires every row to reuse shared-library bytes. The
previous package used native PNG crops; its WEEE crop `7e4de290…` is withdrawn.
All seven printed rows therefore move to the shared variants already used for
JE-1000H.

| Row | Shared variant | Error vs revised AI glyph |
| --- | --- | --- |
| warning | `warning/outline-triangle-tinted` | 0.0118 |
| read manual | `read-manual/book-information` | 0.0138 |
| do not dismantle | `do-not-dismantle/screwdriver-prohibited` | 0.0121 |
| no open flame | `no-open-flame/fire-match-prohibited` | 0.0098 |
| keep away from children | `keep-away-from-children/adult-child-prohibited` | 0.0079 |
| Li-ion | `li-ion/recycle-li-ion-native-dark` | 0.0233 (waived, ceiling 0.024) |
| WEEE | `weee/crossed-bin-bar` | 0.0151 |

Li-ion is the batch-1465 design variation already waived for JE-1000H. The
operator ruled「同 JE-1000H，允许」.

## Battery row source

| Language | Donor printed row | Error |
| --- | --- | --- |
| pt, nl, pl | JE-2000F `修正版.ai` (`b6587afd…`) p.117/135/153, already bound in its published package | 0.0047 |
| uk | JE-3600A EU 0924 AI (`47a346dc…`) p.94, drawings 745–746; wording equals the published JE-3600A uk Web page | 0.0053 |

The trusted entries `JE1000F-EU-{UK,PT,NL,PL}-WEB-BATTERY` in
`docs/renderers/contracts/symbol_web_only_rows.json` bind each donor row; see
[Reviewed Web-only symbol rows](../build_doc_guide/web-component-admission.md#reviewed-web-only-symbol-rows).
The table layout stays two panels of four, as on the en/de pages of the same manual.

## Validation

- `tests.test_je1000f_eu_shared_symbols`: shared bytes, admission of all 32 rows,
  added text only, approval binding, input hashes and cold replay.
- `derive_shared_symbols.py` rerun leaves the package byte-identical.
- Strict Sphinx (`-W`) for the four new sites; Chromium 1280 and 390 px: 8 images,
  none broken, no horizontal overflow in the table or page.

## Release decision (2026-11-02)

The operator reviewed the before/after renderings at 1280 and 390 px and decided
「上线提交发布」. `approval.json` binds the reviewed Markdown hashes.
