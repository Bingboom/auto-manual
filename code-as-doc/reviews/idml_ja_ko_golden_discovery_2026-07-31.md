# Japanese and Korean IDML Golden Discovery (2026-07-31)

Scope: Workstream W / Stage 5 item 9.

## Finding

The existing golden harness had one active assertion for the English
`composed` package. A French snapshot directory existed, but the test did not
execute it. The language adapter copied the English bundle and changed only
`HBApplyLang`; semantic pages kept their `_en.rst` names and English payloads.

A first naive Japanese/Korean regeneration exposed the consequence: French,
Japanese, and Korean produced the same 83-part package. The result was not an
exporter cache leak. Page-language inspection showed that the data pages still
resolved to English, while the shared TOC fallback continued to provide the
same English/French/Spanish source payload. A nominal CJK variant therefore
contained no CJK source text to protect.

## Safety-net decision

The golden fixture adapter now creates a target-language prepared bundle for
Japanese and Korean:

- representative prose, safety, maintenance, list-table, symbol, LCD,
  troubleshooting, and specification copy is localized;
- `_en.rst` semantic pages are renamed to the target suffix and the prepared
  `index.rst` includes are updated;
- required replacements fail loudly if the shared synthetic fixture drifts;
- each built package must contain language-specific Japanese or Korean
  sentinels; and
- every variant is built twice, with byte equality required, while Japanese
  and Korean must remain byte-distinct.

The committed snapshots each contain 89 package parts. Their aggregate
fixture hashes at creation are:

- Japanese: `85aab64216bc9c1a631541a5aa53ea66d8fadd25ac5cd48d24abfbb4dc19af5f`
- Korean: `e077eca6490c8e88da967fd1112258e8c74dc7cb809cd63d46c1e46ca232b119`

## Boundary

This is test-only evidence. It does not enable Japanese or Korean production
delivery, select a CJK font family, change line estimation, modify production
phase2 data, or alter the approved reference-layout contract. Those behavior
changes remain behind the separate Stage 5 operator gate.
