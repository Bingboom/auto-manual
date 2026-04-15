Diff-report fixture scenarios:

- `template_backmap`: template variable rows should map back to the spec source row.
- `placeholder_label_rename`: label-only edits should stay a modified pair, not split into add/delete rows.
- `section_order_fallback`: unmapped fields in the same section should still pair by section order.
