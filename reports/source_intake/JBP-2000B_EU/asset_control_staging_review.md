# Asset-control staging review: JBP-2000B_EU

- Writes are blocked until the operator says `入库`.
- Source record: `recvtPCUCO3Jgp` (`source/manual_jbp2000b_eu_master_normalized`).
- Definitions: 10 approved, build-eligible records.
- Exports: 128 = 54 archive pages + 54 previews + 20 semantic exports.
- All definition/export rows link to the new source record; no write targets the legacy illustration table.
- Phase 2 intentionally contains symbolic asset-record references. They are resolved only after phase-1 definition create + full readback, preventing broken links.

## Definitions

| asset_key | page | language | policy | gate |
| --- | ---: | --- | --- | --- |
| `page/jbp2000b_eu/cover` | 1 | en | localized-full-page | approved |
| `connections/jbp2000b/eu/stack_clearance` | 9 | shared | fixed-product-markings | approved |
| `connections/jbp2000b/eu/locking_en` | 10 | en | localized-full-page | approved |
| `connections/jbp2000b/eu/locking_fr` | 18 | fr | localized-full-page | approved |
| `connections/jbp2000b/eu/locking_es` | 26 | es | localized-full-page | approved |
| `connections/jbp2000b/eu/locking_de` | 34 | de | localized-full-page | approved |
| `connections/jbp2000b/eu/locking_it` | 42 | it | localized-full-page | approved |
| `connections/jbp2000b/eu/locking_uk` | 50 | uk | localized-full-page | approved |
| `charging/jbp2000b/eu/ac_wall` | 11 | shared | fixed-product-markings | approved |
| `charging/jbp2000b/eu/solar` | 11 | shared | fixed-product-markings | approved |
