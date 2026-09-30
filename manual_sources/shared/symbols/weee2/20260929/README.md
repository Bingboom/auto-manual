# Shared battery separate-collection symbol (weee2)

Operator approved the before/after pixels on 2026-09-29. The source is the
approved JE-2000F EU English PDF, page 7; source SHA-256, retained native
vector path indices, crop and output hash are in `candidate-provenance.json`.
Only the symbol paths are retained; no table lines, cell background, text,
or lower WEEE bar are included. This language-neutral symbol is shared across
portable power stations through `symbols/weee2`.

The canonical PNG is `docs/templates/word_template/common_assets/symbols/weee2.png`:
492 x 519 pixels, transparent RGBA. The retained vector PDF and SVG here are
source evidence. Regenerate the PNG by opening `weee2-vector.pdf` with PyMuPDF
and rendering page 0 with `matrix=fitz.Matrix(24, 24), alpha=True`.
The battery symbol (`weee2`) and the electrical-equipment symbol with a lower
bar (`weee`) remain separate asset identities.

Live source: business Base `LD3lb4G1ua4GOVs1vxAc9W2enje`, Symbols
`rec277z0GFV87J/Figure`; asset export `recvuCHOujnTWI/export_file`.
Existing published releases retain their frozen bytes until republished.
