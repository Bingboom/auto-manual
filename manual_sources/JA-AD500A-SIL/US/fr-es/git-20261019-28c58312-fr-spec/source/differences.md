# Differences from the base edition

Base: [`git-20261016-28c58312-solar-voc`](../../git-20261016-28c58312-solar-voc/README.md), the live French/Spanish solar-Voc edition (MA-312). This edition is French only.
Every copied French `source/` and `assets/` file is byte-identical to the base, apart from the label correction and the shared-style migration listed below. The Spanish pages and the base's own `source/approval.json` and `source/differences.md` are not copied.

| Page | Row | Base (printed p.14) | This edition | Reason |
| --- | --- | --- | --- | --- |
| `source/page/spec_fr.rst` (PORTS D’ENTRÉE/SORTIE) | 11 V–16 V⎓8 A max. / 16 V–60 V⎓13 A max., double à 24 A max./500 W max. | Sortie CC | Entrée CC | These rows are the module's DC inputs (car socket and PV), as in the English and Spanish editions. Operator instruction 2026-10-19: 「法语版规格表 Input/Output 写反了 == 这个改掉发布」. |
| `source/page/spec_fr.rst` (PORTS D’ENTRÉE/SORTIE) | 42V–58V⎓10,7A max. | Entrée CC | Sortie CC | This row is the module's DC output to the connected product. |

Shared-style migration (no copy change; see `README.md`): `source/page/product_overview_fr.rst` and `source/page/contact_fr.rst` replace page-local classes and inline styles with shared theme classes. The new `source/presentation.css` holds geometry only, so the re-frozen locale passes the prepared-document shared-style gate.

Not changed:

- `source/native_copy.json` remains the verbatim transcription of the printed PDF (`source/original.pdf`), which still carries the swapped labels; the design source needs its own correction.
- Every other retained French source concern (overview wording, warranty phrasing) is untouched.
- The rendered visible copy is otherwise identical to the base edition. The shared Web stylesheet follows current `main`, as every re-render does.
