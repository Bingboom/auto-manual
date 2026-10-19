# JP intake discovery and phased plan

Target confirmed on PDF cover: JA-AD500A-SIL / JP / ja. Source: operator-supplied
`Jackery DC Input Module取扱説明書V2.0-20260525.pdf`, 10 physical pages,
SHA256 ac3a1f820d94277f6c1a667bafddfa930363b1d74fb084eb7bed43b1c3749777.
Filename states V2.0 / 20260525; no printed version string found. PDF metadata
creation/modification is 2026-05-06, not inferred as the manual version.
Physical 1 cover, 2–9 printed 01–08, 10 QR back cover.

Isolation: managed dc-input-jp-web worktree, branch feat/web-ja-ad500a-sil-jp.
Root tmp and all other worktrees/artifacts retained. start_branch.sh fetched
origin/main but cannot switch main while it is attached to the primary tree;
the clean detached worktree was branched explicitly from refreshed origin/main.
Baseline eb00c120a. No prior JP package found in the local Git inventory.

1. Inventory and source audit: preserve original PDF and native page text.
2. Assets: reuse approved und-locale overview and module bytes; extract JP
   manual, solar/car and QR only after concrete comparison recorded below.
3. Prepared RST → manual-ir/v2 → shared Web/MyST using existing charger-v1
   profile and ReferenceFigure, Inbox, Specs, Callout and Warranty components.
   Add only JP target metadata to existing overlay registry, no per-model config.
4. Hash admission, strict Sphinx, cold replay, negative tamper check, native
   copy/parameter/heading parity, resource/fragment and 1280/390 browser QC.
5. Commit source/package/evidence and open a validated draft engineering PR.

No merge, Hello-Docs release, business-plane table/queue/asset/HTML_link write.
Production edits are confined to this package and the existing target overlay.

| Slot | Inspected candidates | Identity/content | Decision and concrete reason | Boundary policy |
| --- | --- | --- | --- | --- |
| Overview | US reviewed assets/overview-textless.png + PDF | Identical JA-AD500A-SIL silhouette, ports, loop, markings and leaders | Byte-exact reuse; 5 JP lines replace 6 US lines | Full figure and leaders retained; white canvas |
| Inbox module | US reviewed assets/inbox-module.png | Same source product object | Byte-exact reuse | Complete object/markings |
| Inbox manual | US reviewed assets/inbox-manual.png; shared/template inventory | English cover/US contact does not match Japanese cover | Extract physical 2 Japanese booklet only | Entire booklet frame, source cover text retained as object artwork |
| Solar | US reviewed assets/solar.png; target and shared assets | US panel positions/callout differ; includes SolarSaga 100 Air x4 wording absent from JP | Extract complete JP physical 4 panel; live DC8020 | All panel edges, leader, sun, cables and product markings retained |
| Car | US reviewed assets/car.png; target and shared assets | Host AC socket geometry differs from JP; existing base lacks JP capsule layout | Extract physical 6 full JP panel; strip external labels + isolated caption capsule, restore via shared CSS | Whole panel, connectors and cables retained |
| QR | US reviewed contact QR and shared assets | US destination unfit for Japan; JP has its own back-cover code | Extract physical 10 QR including quiet zone | Full code; no inferred destination |

Source concerns retained: cover references safety chapter not present as a
separate chapter; specs print 出カ; 8A input vs 12V/10A vehicle description;
module 16–60V vs host 36.8–56V / 40–57.6V; warranty refers to portable power
products; concatenated wording in voltage warning and warranty geographic
scope. Source wraps are joined; no technical or legal correction is invented.
