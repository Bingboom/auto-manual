# JA-AD500A-SIL / JP / ja Web candidate

This Git-only Japanese candidate is sourced exclusively from the supplied
`Jackery DC Input Module取扱説明書V2.0-20260525.pdf`. The cover identifies
JA-AD500A-SIL and says 国内専用/For use only in Japan. SHA-256:
`ac3a1f820d94277f6c1a667bafddfa930363b1d74fb084eb7bed43b1c3749777`.
The original PDF is checked in byte-exact. Physical 1 is the cover, 2–9 are
printed 01–08, and 10 is the QR back cover. The filename states V2.0 and
20260525; no printed version is visible; PDF metadata is dated 2026-05-06.

`source/page/` is the editable Japanese RST source. `source/native_pages.json`
retains extracted PDF text and geometry; `source_manifest.json` binds source,
assets, target, page mapping and input hashes. `web/ja/` freezes semantic
manual-ir/v2, shared MyST, stylesheet and content-addressed assets. Headings,
body, tables, warning/guarantee clauses and diagram annotations are selectable.
Booklet artwork naturally contains its miniature printed cover. No page image
stands in for manual body copy. Contact details stay in an untitled page-end
block; the QR is the Japanese original, including its quiet zone.

This target uses the existing prepared RST → manual-ir/v2 → shared Web/MyST
route and charger-v1 skeleton; the single new JP overlay only selects existing
contracts. There is no new family configuration, renderer, phase2 registration,
or live data dependency. Inbox, ReferenceFigure, Callout, Specs and Warranty
all pass real component discovery/count admission. Warranty keeps the source
one-year sentence and six sections, rather than adding an unprinted year badge.

Asset decisions are documented before extraction in `DISCOVERY.md`. Existing
module and und-locale overview PNG/PDF are reused byte-exact from the reviewed
same-model package; their source paths/hashes are recorded. Japanese solar
arrangement, host socket, booklet and QR differ, so their four exports use the
existing hash-pinned asset pipeline. Full panel borders, cables, product
markings and leaders remain; car caption text and its independent gray capsule
are removed together and rebuilt through shared CSS. All figure annotations
are editable Japanese. The overview is bounded at 40rem and scales to phone
width; the LED table uses the existing three-column grid with wrapping cells.

## Source differences retained for review

- Cover refers to 安全上のご注意 without a standalone safety chapter in this PDF.
- Specifications print 入力/出カポート and DC 出カ (katakana カ).
- Module input is 8A for 11V–16V; car charging copy specifies 12V/10A.
- Module PV is 16V–60V while H1/Battery Pack ranges are 36.8V～56V / 40V～57.6V.
- Warranty calls this a portable-power product. Geographic scope and voltage
  warning concatenate phrases. These words are retained verbatim.
- Solar layout differs from US; US SolarSaga 100 Air ×4 labeling is absent.
- Japanese warranty has 30/31-day exchange/repair terms, paid repair and 90-day
  repair guarantee. No US terms, battery-cell exclusion, translation or numeric
  correction was substituted.

Only source line wrapping, decorative list markers and print page numbers are
normalized. The cover preface is retained; the booklet's duplicate tiny cover
copy is represented by its complete object image. Evidence explains those
boundaries separately from primary selectable body checks.

## Rebuild

Run from the repository root with a fresh output directory:

```sh
python3 manual_sources/JA-AD500A-SIL/JP/ja/git-20261008-ac3a1f82/render.py /tmp/dc-input-jp-new
python3 -m sphinx -W --keep-going -b html /tmp/dc-input-jp-new /tmp/dc-input-jp-html-new
python3 -m http.server 18988 --bind 127.0.0.1 --directory /tmp/dc-input-jp-html-new
```

The adapter validates frozen source/repository hashes, then calls the existing
shared export and replay APIs. A changed input or wrong component inventory
fails closed. Cold IR replay requires only frozen IR, stylesheet and assets;
it never reads the original PDF or RST. `evidence/` and `output_inventory.json`
record build, replay, source/asset comparison and actual browser acceptance.
Local preview is a review candidate. Source/layout confirmation, merge and
Hello-Docs/RTD publication remain separate operator-owned stages.

No Feishu Base, source table, queue, online asset registry, build record or
HTML_link write is part of this change. No approval has been inferred from the
reviewed US package.
