# JBP-2000B EU uk/pt/nl/pl acceptance candidate

Agent verification completed on 2026-10-07. Final layout is revision r2; `sealed/` retains the retired r1 layout checkpoint, and `sealed-r2/` contains the final receipts. Operator review, merge and online publication are pending. This record is not an independent human approval. MA-257 explicitly excludes additional online languages.

Target/source, original SHA, native physical pages, baseline reproduction and frozen replay procedure are documented in `manual_sources/JBP-2000B/EU/native-0924/README.md`. Native source controls all four locale bodies; the approved English release controls shared structure. Existing five locale files and published bodies are unchanged.

## Native copy review

158 Ukrainian and 160 Portuguese/Dutch/Polish source-backed fields are mapped. Mapped English paragraph residuals are empty. Native specs retain JBP-2000B, 2048Wh, LiFePO4, 14.8kg, 36.5×25.5×19.1cm, 6000 cycles/70%+, 36.8–57.6V/75A and −10–45°C; fault codes F0/F3/F4/F5/F8/FE/FF and warranty 3+2-year source badges are retained. Page80 manufacturer address, phone, email, RED directive and declaration URL agree with the reference; shared legal content stays English, as printed.

Ukrainian frontmatter has no dual-host compatibility note; none was added. Its body names Jackery Explorer 2000 Plus. Other three locales retain the printed E1000 Plus V2/E2000 Plus V2 note. Ukrainian Exchange text is German (`Umtausch`, `Jackery tauscht…`), and lower symbol header is `имвол`; both are retained. Portuguese ON/Apagado, Dutch INGANGS//UITGANGSPOORTEN and native recyclingcen- trum/afvalverwerkings- dienst printed wrap hyphens are retained. These are source findings, not new translations. Full exceptions are in each copy map.

Native symbol panel geometry is six items left and two right, with battery WEEE above equipment WEEE. Every caption and glyph is bound to its actual native source row; source-backed symbol admission passes 8/8 for each locale. Maximum mean channel error is below the fixed 0.02 gate. Complete native overview and LCD panels are cropped once per locale; LCD descriptions use HB-TABLE-REFERENCE, with no fabricated numbered column.

## Artwork inventory and reuse decisions

| Candidate / role | Decision and source | Identity / background |
| --- | --- | --- |
| Inbox3, LCD-control, clearance, AC, solar | Reuse English baseline packaged files unchanged | Same target; preserve native panels and all edges |
| Warning/book/dismantle/flame/children | Reuse checked shared/symbols variants unchanged | Correct native glyphs; genuine transparency; row-by-row source comparisons |
| Equipment WEEE | Reuse shared crossed-bin-bar PNG unchanged | Bar retained; source bottom-right caption |
| Battery WEEE | Reuse je100c_eu_shared/symbol_battery_weee.png unchanged; expose explicit shared no-bar key | No bar; source upper-right caption; genuine transparency |
| Li-ion | Existing PNG and generic shared SVG fail native glyph comparison; select original HTP017 vectors into source-specific shared candidate | Original PDF paths/ancestors, transparent margins; no color-based deletion |
| Inline ×5 | Reuse JBP-3600A reviewed transparent connection-x5.png unchanged | Source image identity visually checked; ×5, not ×8 |
| Overview/LCD | Native dense labels differ; crop each source finished panel | Bounded native labels; preserve panel geometry |
| Main power | Existing panel has English external labels/clock; extract neutral original page10 panel using recorded recipe | Preserve product marks, hands and clipping; live native instructions and CSS 3s clock |
| Locking | Existing panel has baked English caption pills; extract neutral original page12 complete panel using recorded recipe | Preserve gray background and original clipping; remove only external pills and use shared CSS native badges |

Each page has20 visible images:15 reused assets and5 newly sourced panels/glyphs. All packaged bytes and provenance are frozen in the source manifest. Native neutral panel hashes: power `af29680d9135da5907c8a841c42f860276fa2bce1d2f83cdab3c2512607a853b`; locking `9e09181b8709b59dc8bb6cd07ad0647fed92b8fe99a348862d6f076d274a7d8a`.

The initial vector replay experiment lost PDF clipping and was rejected; it is not shipped. Current before/after image pairs and12x corner checks are under `artwork/`. Source hands, button faces, full frame edges and numeric1/2 are preserved. Caption-frame admission passes, with measured baked-fill fractions recorded by the final caption-frame gate. No asset registry or Base was written.

## Validation

- Four cold IR replays produce byte-identical MyST.
- Fresh source-specific component admission passes with no legacy debt in all four locales.
- Source-bound symbol admission:32/32 rows pass; caption-frame admission:8/8 labels pass.
- Four strict Sphinx HTML builds pass with `-W --keep-going`.
- Browser1280×900 and390×844:8/8 checks,20/20 decoded images per page, zero horizontal overflow, one CSS clock each, native lock labels fit and intersect none of the four source step-digit regions (each checked with a1pt expanded margin). On mobile, native locking labels stack below the complete panel; on desktop they stay inside the left source margin, before the step numbers. `browser/metrics.json` and screenshots record the actual pages.
- Existing policy/coverage/symbol/frame/frozen-evidence tests:60 tests pass.
- Maintainer guardrails pass.

Only owned candidate unused assets were pruned. Primary `tmp/`, historical packages, other worktrees, Base, queues, workflows, dependencies, schemas and CLI are untouched. Final engineering PR/CI, merge, mirror, publication PR and RTD/live acceptance remain separate gates.

The r1 mobile overlay let long native labels cover step1. Revision r2 uses the existing shared stacked mobile treatment and a narrower desktop caption region. All eight viewport cases were repeated and verified with zero covered step-digit regions. Native copy and artwork bytes remain unchanged.
