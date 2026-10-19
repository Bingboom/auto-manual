# Build guide: common mistakes and troubleshooting

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 7. Common Mistakes

- Editing [`docs/_build/**`](../../docs/_build) as if it were the authoring surface
- Creating a new config only because the model changed
- Using `review --refresh-review` when only parameter pages need to be synced
- Forgetting to commit `_review/<model>/<region>/` after each review round
- Treating `_build/rst` and `_review` as the same thing
- Putting review metadata in `overrides/` and expecting it to overlay; only `_assets`, `_static`, and `renderers` are copied into the runtime bundle
- Letting `build.py`, `tools/build/docs.py`, or `tools/build_queue/process_build_queue.py` absorb new low-level implementation instead of pushing that logic into helper modules

## 8. Minimal Troubleshooting

For JE-1000F/JP, `build.py md --config configs/config.ja.yaml --model JE-1000F
--region JP --source runtime` supports the authored text-only inbox table and
its following notes. The document adapter preserves a nonempty, one-row,
three-column inventory with no images and no immediately adjacent table.
Illustrated inbox compositions still require their three images and tip table.
No placeholder images or synthetic tip copy are added.

The prepared-bundle IR adapter distinguishes complete, multi-row signal-word
definitions from single notice callouts using the shared label vocabulary.
Each definition row needs two nonempty cells and a distinct recognized label;
malformed tables beginning with a known signal word still fail. See the
[same-source IR contract](../dev/latex_indesign_same_source_plan.md) for the boundary.

The JP symbols introduction's plain boxed heading and two following paragraphs
now enter IR as editable heading/body blocks. The existing dedicated
`tools/manual_ir_cli.py --strict` check on the prepared runtime bundle reports
zero skipped blocks. The parser accepts only the complete supported shape;
unknown TeX content still fails strict extraction. PDF source geometry is
preserved; native InDesign layout acceptance remains a separate check.

For measured fallback IDML plans, operation subsections now flow naturally
instead of inheriting an extra final-page break from the legacy four-page
assumption. Specification shells reserve the emitted cells' widths, insets
and wrapped line heights. Approved reference, compact and no-plan export
geometry stays unchanged. The single-character Celsius unit (`℃`) uses the
existing bundled Noto Sans fallback without rewriting source copy. Native
save/reopen and exported-PDF glyph checks are both required: zero overset
alone does not prove a printable PDF. See the
[JP native repair record](../reviews/je1000f_jp_native_overflow_2026-09.md).

`Failed to resolve Product Name from Spec_Master.csv`

- Check [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv) for `Row_key=product_name`
- Check model / region / language coverage
- Run `python build.py check --config ... --model ... --region ...`

Review bundle not found

- Seed it first with `python build.py review --config ... --model ... --region ...`

Need to rebuild the first draft from template/data only

- Use `--source runtime`

Need to release from reviewed text only

- Use `python build.py publish --config ... --model ... --region ...`

`STALE_IDENTITY_LITERAL` or another model name is reported during `check`

- fix the template or review text if the model mention is stale
- if the foreign literal is intentional, add it to `checks.allowed_foreign_identity_literals`
