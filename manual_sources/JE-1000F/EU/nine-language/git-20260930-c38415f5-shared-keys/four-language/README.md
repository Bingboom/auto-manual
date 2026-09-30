# JE-1000F EU shared key combinations

Version: git-20260930-c38415f5-shared-keys

Migrates the uk/pt/nl/pl frozen key-combination table to the existing
HB-TABLE-KEY-COMBINATIONS ComponentSpec and public Web renderer.
All cell text, other IR blocks, rendered content outside this table, images,
and reviewed corrections are preserved from the previous source package.
No live data, PDF extraction or model-specific CSS is required.

Each locale passed full-text equality, table-excluded HTML equality,
image hash equality, PDF-free repeat replay and strict Sphinx build.
See migration_receipt.json for validation results and source_manifest.json
for the immutable source chain.
