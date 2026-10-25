# JE-3000C KR Korean Web candidate

Source: `source/original.pdf` (20 retained portrait pages; SHA-256 in `source_manifest.json`). The user requested removal of the original manufacturing landscape sheet. The untouched 21-page original remains in the source folder's `原始PDF备份` directory outside Git.

This is the MA-348 approved Git-only Web source. It uses the shared Manual IR / registered component Web consumer and frozen local assets. It does not access online tables, enqueue a business build, or alter print-review files. The 2026-10-24 operator grant authorizes this engineering PR and its generated publication PR under the all-checks-green protocol.

The Web body starts at **중요**. Cover title, model/locale/customer-email block, blank pages and manufacturing QR back cover are omitted from the Web body. The PDF retains all twenty pages. The only approved text erratum restores `처음 사용하기 전에 제품을 완전히 충전하십시오.` on printed page 10; it is recorded in the manifest and changes only the Web candidate.

## Replay

From the repository root, using the project Python environment:

```sh
python manual_sources/JE-3000C/KR/ko/git-20261021-78316033/rebuild.py --output /tmp/je3000c-kr-ko-source
python -m sphinx -W --keep-going -b html /tmp/je3000c-kr-ko-source /tmp/je3000c-kr-ko-html
```

Both output directories must be fresh. The assembler verifies all frozen inputs and shared-code pins before writing output. `web/ko` holds the portable serialized IR, Markdown, shared CSS/scaffold and local assets. `source/asset_inventory.json` records prior candidates; `source/asset_decisions.json` records reuse, hashes and source crop rectangles. The connected front/right overview stays a single complete panel.

## Verification

See `validation/content-audit.json` and `source/pdf-edit-verification.json`. Native prose, LCD descriptions, fault measures and specifications remain selectable and searchable. Dense localized operation/overview panels and native App frames retain their approved artwork. The LCD table has 26 rows; high/low temperature intentionally share source number 21. The source PDF's thresholds and binding prompt are preserved without translation changes.

Shared-component style admission and strict Sphinx passed. A cold replay reproduced the same Markdown and rejected a deliberately corrupted illustration. Thirty-four targeted shared-contract tests passed. Desktop/mobile previews were visually reviewed. This is conversion verification, not a renewed engineering approval of source technical specifications or a publication acceptance.

## 2026-10-21 style correction and release gate

Chapter headings use the shared H1 scale and subsection headings use H2; the preface IMPORTANT label is a strong paragraph. Five warranty sections are registered rounded-card components, with a separate warranty-period card. Spec group headings remain H2 under the specification chapter. All wording, periods and values are preserved.

Source-bound glyph/caption admission now passes for all seven symbol rows. Four shared variants are reused byte-for-byte and three exact original-PDF vector variants are added to the shared catalog under MA-348. Historical frozen packages retain their bytes and recorded handling. The repository US regression check and source replay remain distinct from technical approval of the PDF values.

## 2026-10-24 LCD status label formatting

All 23 LCD description prefixes (`켜짐:`, `점멸:`, `꺼짐:`) use semantic strong emphasis, including the colon. Only the status labels are bold; descriptions, row order, values and source wording are unchanged. The prepared source, serialized IR, generated Markdown and input hashes are updated together.

This implements the corpus [status-word contract](../../../../../code-as-doc/dev/translation_corpus_governance.md#6-status-word-contract-shared-boundary-with-the-build), rather than a Korean-only or preview-only styling exception.

## 2026-10-24 App step caption centering

Live step numbers 2.1–2.5 align with each native phone frame center, using the existing shared `caption_centers_pct` metadata instead of equally dividing the complete image canvas. The two- and three-phone panels keep their original bytes and complete frames. Measured image-space bounds and percentages are recorded in `source/asset_decisions.json`; the prepared source, IR and frozen Markdown carry the same placement.

## 2026-10-24 release admission

MA-348 records the operator grant `推送上线`. Seven symbols bind to exact PDF page-4 glyphs, caption rectangles and hashes; the original filename is retained separately from the relative packaged PDF path consumed by sealing. Source replay uses the synchronized shared toolchain, retains 23 bold LCD status prefixes and five source-centered App captions, and preserves all source wording and values. `validation/content-audit.json` records admission results.
