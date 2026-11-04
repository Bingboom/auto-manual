# JE-3000B / US / en — current source alignment candidate

Record `reczz28SlRGJim2Y`; current single-language attachment SHA-256 `bd8a82962865ae64cd52e9c6ebf9a20d8495652773ba09806d1911cb0f360294` (19 pages). Review scope is physical p2 and p4–19. Front cover and paper TOC are excluded by explicit operator instruction; contact information is retained. The previous frozen edition remains unchanged.

This candidate restores safety/FCC columns, source warning lockups, merged LCD number/icon cells, six original illustration frames with native text in its original position, vertical LCD mode layout, troubleshooting grid, specification hierarchy/line breaks and contact glyphs/QR. All inherited conversion declarations are adjudicated in `source/differences.md`. No inferred technical corrections or foreign-model facts are introduced.

Rebuild from committed `source/en/content.json` with `refresh_manifest.py`, then `rebuild.py --output <unused-directory>`, followed by strict Sphinx. `build_content.py`, `derive_assets.py` and `source/asset_recipe.json` describe the historical intake; do not rerun them over the corrected candidate. Current panel extraction and added glyph provenance are in `source/current-*.json`. Body text and tables remain native. Original artwork is retained; no manual redraw or whole-page raster is used.

The local acceptance evidence is `audit/current-source-review/`. Full source-to-web and reverse copy, numeric conditions, complete desktop/mobile viewport coverage, contained scrolling, and file-resource checks are separate from build success. Run `refresh_manifest.py frozen` only after storing verified Web output and evidence. The inherited first-pass `evidence/` is superseded by this complete audit.

Operator authority: “一个一个修 复核通过 就打钩”, “本地构建复核通过就可以了”, “网页版 不需要封面”, and authorized isolated parallel work. MA-381 concerns later integration. Publication eligibility remains false; local checkbox acceptance does not claim release, deployment, or personal operator visual approval.

## Authorized release snapshot

This immutable -release copy binds the fully reviewed candidate at cd3703837dfc119790906351486d1517772572eb under MA-381 (operator: 授权本批逐本全绿后合入上线; local acceptance: 本地构建复核通过就可以了). Candidate content, CSS and artwork remain unchanged. Original repo_inputs pins are preserved. Current approval and byte-equivalence evidence supersede inherited candidate-status statements for this copy only. Publication itself remains a separate transaction.
