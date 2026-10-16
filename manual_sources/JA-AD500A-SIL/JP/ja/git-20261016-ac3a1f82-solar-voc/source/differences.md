# Differences from the base edition

Base: [`git-20261009-ac3a1f82-web-layout`](../../git-20261009-ac3a1f82-web-layout/README.md), the live Web-layout edition of the approved package (MA-272).
Every copied `source/` and `assets/` file is byte-identical to the base except the copy correction below and the shared-style migration listed after it. The base edition's own `source/approval.json` and `source/differences.md` are not carried over.

| Page | Base (printed p.5) | This edition | Reason |
| --- | --- | --- | --- |
| `source/page/charging_ja.rst` (solar charging) | Jackeryブランド以外の付属品を使用して充電しないでください。ソーラーパネルの開放電圧（Voc）が、Jackery SlimPower H1 のDC入力範囲（36.8V～56V）または Jackery Battery PackのDC入力範囲（40V～57.6V）内であることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。 | Jackery DC Input Moduleを介して接続した製品を充電する場合は、Jackery製ソーラーパネルの使用を推奨します。接続するソーラーパネルの開放電圧（Voc）が、本モジュールのDC入力電圧範囲（16V～60V）内であることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。 | Panels connect through the module, so the governing limit is the module's DC input voltage range (16V～60V, spec table 「DC 入力」); the printed text cites the downstream SlimPower H1 / Battery Pack ranges. Operator instruction 2026-10-15/16: replace the paragraph and keep the disclaimer; the opening accessory warning is dropped because it contradicted the recommendation and the disclaimer (“删掉第①句”); wording follows the operator-approved Japanese translation. |

Shared-style migration (no copy change; see `README.md`): `source/page/00_preface_ja.rst`, `charging_ja.rst`, `spec_ja.rst`, `product_overview_ja.rst` and `contact_ja.rst` swap page-local classes and inline styles for shared theme classes, and `source/presentation.css` keeps geometry only, so that the re-frozen locale passes the prepared-document shared-style gate.

Not changed:

- `source/native_pages.json` remains the verbatim text of the printed PDF (`source/original.pdf`), which still carries the old wording; the design source needs its own correction.
- Every other retained source concern (vehicle current text, 出カ labels, warranty phrasing) is untouched.
- The rendered visible copy is otherwise identical to the base edition. The shared Web stylesheet follows current `main`, as every re-render does.
