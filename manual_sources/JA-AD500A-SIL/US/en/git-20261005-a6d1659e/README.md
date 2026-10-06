# Jackery DC Input Module — English Web intake

This is a Git-only **review candidate**, not a published or operator-confirmed
English baseline. The public model printed on the supplied source is
**JA-AD500A-SIL**, region **US**. HTO889A is the source project identifier.

`source/original.ai` is the byte-exact operator source. `source/panel_map.json`
maps its single Illustrator artboard to six English body panels and the
cover/back. `source/page/` contains native, selectable copy. The specification
table preserves its two-row DC Input label, and the warranty is 12 months.
The source's battery-cell exclusion is retained verbatim for review; no paper
version has been inferred.

The solar diagram preserves **SolarSaga 100 Air × 4** and the original **DC8020**
label at its leader endpoint, following the operator's instruction
“这个dc8020直接保留在底图”. It has no duplicate live DC8020 caption. Car labels
use the existing ReferenceFigure overlay, including on mobile. The artwork
recipe records the inventory/reuse decisions and pins all six extracted images;
these assets have not been promoted to an online registry.

## Rebuild

From the repository root, with the project's Python dependencies installed:

```sh
python manual_sources/JA-AD500A-SIL/US/en/git-20261005-a6d1659e/render.py /tmp/jaad500a-web-new
python -m sphinx -W -b html /tmp/jaad500a-web-new /tmp/jaad500a-html-new
python -m http.server 18979 --bind 127.0.0.1 --directory /tmp/jaad500a-html-new
```

The output directory must be new and outside this input snapshot. The adapter
verifies frozen source and repository inputs, then uses the existing prepared
RST → manual-ir/v2 → shared Web/MyST pipeline. It does not implement an HTML
renderer or register a phase2 target. `web/en/` contains the frozen MyST, IR,
CSS and packaged artwork. `output_inventory.json` records output/evidence
hashes separately from source inputs.

## Verification and scope

- Strict Sphinx and a source-free cold IR replay passed. Cold replay preserves
  body text and rejects a changed solar asset.
- 38 focused component tests and 20 overlay contract tests passed, as did Ruff,
  maintainability guardrails and documentation link/lifecycle checks.
- The JE-1000F/US/en repository regression passed with the committed
  `tests/fixtures/phase2` snapshot. The default command could not resolve its
  product because this worktree has no local Spec_Master snapshot; the retained
  log makes that limitation explicit. This regression does not validate this
  new model's copy.
- Actual browser inspection at 1440px desktop and 390px mobile found all six
  images loaded, no document horizontal overflow or broken fragment links,
  and intact native specifications/warranty. See `evidence/verification.json`
  and the browser screenshots. Sphinx log copies omit trailing terminal spaces;
  original session logs remain in the retained discovery directory. The LED table uses its shared horizontal scroll
  surface on small screens.

No live source table, queue, asset registry, build record or HTML_link was
written. Merge, Hello-Docs publication, RTD and other languages require their
own next-stage instruction. English baseline confirmation remains pending.
