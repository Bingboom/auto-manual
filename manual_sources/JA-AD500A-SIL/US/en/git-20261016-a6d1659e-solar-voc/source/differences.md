# Differences from the approved package

Base: [`git-20261006-a6d1659e-reviewed`](../../git-20261006-a6d1659e-reviewed/README.md) (MA-259).
Every `source/` and `assets/` file is byte-identical to the base except the one page below.

| Page | Printed / approved | This edition | Reason |
| --- | --- | --- | --- |
| `source/page/charging_en.rst` (printed p.3, solar charging) | …Ensure that the open-circuit voltage (V<sub>oc</sub>) of the solar panel is within the DC input range (36.8V–56V) of the Jackery FridgeGuard or the DC input range (40V–57.6V) of the Jackery Battery Pack. … | It is recommended to use Jackery solar panels to charge the connected product through the Jackery DC Input Module. Ensure that the open-circuit voltage (V<sub>oc</sub>) of the connected solar panels is within the module's DC input voltage range (16V–60V). Jackery is not responsible for any damage or loss resulting from the use of third-party solar panels. | Panels connect through the module, so the governing limit is the module's DC input voltage range (16V–60V, spec table "DC Input"); the printed text cites the downstream FridgeGuard / Battery Pack ranges. Operator instruction 2026-10-15: replace the paragraph, keep the disclaimer. |

Not changed:

- The printed source (`source/original.ai`) still carries the old wording; the design source needs its own correction.
- The rendered Markdown is otherwise byte-identical to the approved release. The shared Web stylesheet (`web_manual.css`) follows current `main`, as every re-render does; it carries no rule specific to this manual.
