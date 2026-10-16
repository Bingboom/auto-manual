# Differences from the approved edition

Base: [`git-20261008-efb663e3-no-cover-reviewed`](../../git-20261008-efb663e3-no-cover-reviewed/README.md) (MA-277).
Every copied file (PDF, `artwork/`, `asset_provenance.json`, `source/`) is byte-identical to the base except `source/chapters.json`, which differs only in the paragraph below.

| Location | Approved (printed p.20, native block 5) | This edition | Reason |
| --- | --- | --- | --- |
| `source/chapters.json`, ソーラー充電 paragraph | Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryのソーラーパネルを使用することをお勧めします。ソーラーパネルの開放電圧（Voc）が、Jackery SlimPower H1のDC入力電圧範囲（36.8V~56V）内に収まっていることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。 | 本製品の充電には、Jackery製ソーラーパネルの使用を推奨します。接続するソーラーパネルの開放電圧（Voc）が、Jackery DC Input ModuleのDC入力電圧範囲（16V～60V）内であることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。 | Panels connect through the Jackery DC Input Module, so the governing limit is the module's DC input voltage range (16V～60V); the printed text cites the H1's own DC input range. Operator instruction 2026-10-15/16: replace the paragraph and keep the disclaimer; the opening accessory warning is dropped because it contradicted the recommendation and the disclaimer (“删掉第①句”); wording follows the operator-approved Japanese translation. |

Not changed:

- `source/native-text.json` remains the verbatim text of the printed PDF, which still carries the old wording; `verify.py` exempts only the declared native block from verbatim coverage and asserts the corrected text instead.
- The troubleshooting F7 step 「本製品の最大DC 入力電圧は56V です。」 is out of scope and unchanged.
- The rendered Markdown is otherwise byte-identical to the approved edition. The shared Web stylesheet and the IR's embedded registry/theme hashes follow current `main`, as every re-render does.
