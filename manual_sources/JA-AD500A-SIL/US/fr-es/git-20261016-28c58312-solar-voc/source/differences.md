# Differences from the approved package

Base: [`git-20261007-28c58312-reviewed`](../../git-20261007-28c58312-reviewed/README.md) (MA-262).
Every `source/` and `assets/` file is byte-identical to the base except the two pages below.

| Page | Printed / approved | This edition | Reason |
| --- | --- | --- | --- |
| `source/page/charging_fr.rst` (printed p.13, solar charging) | …Assurez-vous que la tension en circuit ouvert (Voc) du panneau solaire se situe dans la plage d’entrée CC (36.8 V–56 V) du Jackery FridgeGuard ou dans la plage d’entrée CC (40 V–57.6 V) du Jackery Battery Pack. … | Il est recommandé d’utiliser des panneaux solaires Jackery pour charger le produit connecté via le Jackery DC Input Module. Assurez-vous que la tension en circuit ouvert (Voc) des panneaux solaires connectés se situe dans la plage de tension d’entrée CC du module (16 V–60 V). Jackery décline toute responsabilité en cas de pertes causées par l’utilisation de panneaux solaires d’autres marques. | See below. |
| `source/page/charging_es.rst` (printed p.19, solar charging) | …Asegúrese de que el voltaje de circuito abierto (Voc) del panel solar esté dentro del rango de entrada de CC (36.8 V–56 V) del Jackery FridgeGuard o del rango de entrada de CC (40 V–57.6 V) del Jackery Battery Pack. … | Se recomienda usar paneles solares Jackery para cargar el producto conectado a través del Jackery DC Input Module. Asegúrese de que el voltaje en circuito abierto (Voc) de los paneles solares conectados esté dentro del rango de voltaje de entrada de CC del módulo (16 V–60 V). Jackery no se hace responsable de pérdidas causadas por el uso de paneles solares de otras marcas. | See below. |

Reason: panels connect through the module, so the governing limit is the module's DC input voltage range (16V–60V, spec table "DC Input"); the printed text cites the downstream FridgeGuard / Battery Pack ranges. Operator instruction 2026-10-15: replace the paragraph, keep the disclaimer; wording follows the operator-approved French and Spanish translations.

Not changed:

- `source/native_copy.json` remains the verbatim transcription of the printed PDF (`source/original.pdf`), which still carries the old wording; the design source needs its own correction.
- The other retained source concerns (French spec input/output labels, `Oiture`/`Double to`, Spanish interpretation-rights clause, battery-cell warranty condition) are untouched.
- The rendered Markdown is otherwise byte-identical to the approved release. The shared Web stylesheet (`web_manual.css`) follows current `main`, as every re-render does.
