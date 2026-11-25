# SlimPower H1 JP — Web-layout edition

Operator instruction, 2026-11-25: 「这个卫士1代 有些版面 要调整的 你调整一下」, with nine screenshots of the live page:

- 各部の名称 labels;
- the power-button labels;
- the LCD screen;
- the 縦置 note;
- the wood-wall preparation panel;
- the 主な仕様 groups;
- 保証について;
- the App screenshots;
- App 4.1 / 4.2 and the back-cover QR.

This edition fixes those blocks against the same PDF, together with every block of the same kinds elsewhere on the page.
It is derived from the [approved solar-Voc edition](../git-20261016-efb663e3-solar-voc/README.md) (MA-312). That edition, its printed source and its release evidence remain immutable.

**Status: `operator-approved-git-only-release`.** The operator reviewed candidate `95d63489` on the per-chapter comparison page (print, current Web, new desktop, new phone) and answered 「上线」 on 2026-11-25 (MA-486). The four declared copy differences keep their defaults. `source/approval.json` binds the chapters, presentation, component requirements and every reviewed input, and the IR is publication-eligible. Release is the Git-only Web Publish sealed at the merged `main` commit.

## What changed

Per block, with the PDF page and reason, the full list is in `source/differences.md`. In short:

- **Labelled figures:**
  - Figures: 各部の名称, power button, stand / wood / concrete preparation, App rows 2.1–2.2 and 2.3–2.5.
  - Each is a textless crop of the JP print panel, made with the shared asset pipeline.
  - Every printed line becomes a live label at its print position, with the print weight (`<strong>`), the print type size relative to the panel, and the print alignment.
  - Before, the reused US art drew a different composition, so the JP labels fell on the wrong objects.
  - Narrow print panels keep their print width.
- **Text structure (copy unchanged):**
  - the bold lead of each safety item;
  - one item per line in callouts, troubleshooting and warranty;
  - printed line starts;
  - circled LCD numbers;
  - bold status leads;
  - the App bind note as bullets.
- **Headings:**
  - chapters are the top level, so the specification groups become sections of 主な仕様;
  - the ● lead sentences, the wall types and App 4.1 / 4.2 follow the printed hierarchy;
  - the 使用上のご注意 ■ titles are bold lines;
  - Japanese headings keep their printed case.
- **Shared components:**
  - 保証期間 prints as a section card, not the numeric year badges;
  - the LCD screen uses the shared portrait layout.
- **Art:** the AC-cable card no longer shows the printed card border.

The package stylesheet only adds geometry and type size, never paint. `tests/test_je1000e_wh_jp_web_layout.py` proves the visible copy equals the approved copy apart from the declared differences.

## Reconstruction

`derive_web_layout.py` is the maintenance entrypoint for this edition. A second run leaves the tree unchanged. It:
- copies the approved inputs;
- applies the layout changes;
- renders the changed art with the shared asset pipeline;
- recounts the shared components;
- regenerates the generated tail of `source/presentation.css`;
- refreshes `source_manifest.json`.

The original PDF is stored externally; see the source pointer. Pass a local copy whose SHA-256 matches. `rebuild.py` and `verify.py` are the approved edition's scripts, copied byte-for-byte.

```sh
PKG=manual_sources/JE-1000E-WH/JP/ja/git-20261125-efb663e3-web-layout
PYTHONPATH=. python "$PKG/derive_web_layout.py" --pdf <original.pdf>
PYTHONPATH=. python "$PKG/rebuild.py" --output tmp/h1-layout-cold
python -m sphinx -n -W --keep-going -b html tmp/h1-layout-cold tmp/h1-layout-html
PYTHONPATH=. python "$PKG/verify.py" --html tmp/h1-layout-html/manual.html --pdf <original.pdf>
python -m unittest tests.test_je1000e_wh_jp_web_layout
```

After any source change, replace `web/ja` with a fresh cold replay and run the derivation again.
