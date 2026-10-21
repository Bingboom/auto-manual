# JE-3000C KR Korean Web candidate

Source: `source/original.pdf` (20 retained portrait pages; SHA-256 in `source_manifest.json`). The user requested removal of the original manufacturing landscape sheet. The untouched 21-page original remains in the source folder's `原始PDF备份` directory outside Git.

This is a Git-only candidate. It uses the shared Manual IR / registered component Web consumer and frozen local assets. It does not access online tables, enqueue a business build, alter print-review files, or authorize merge/deployment.

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
