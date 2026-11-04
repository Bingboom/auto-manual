# JHP-2000A-RC US V2 — source discovery and artwork reuse record

Recorded before extraction, per the Web artwork reuse order
(`docs/renderers/contracts/STYLE_DEFINITION/web-artwork-reuse.md`).

## Source

- 发布文档管理 record `reczz28SPRx9pzTt` (物料号 16-0102-000417, 项目号 HTE2606, 客户型号 JHP-2000A-RC,
  sku 21-0001-000518 / 21-0001-000623), field 单语言说明书: 「【Jackery HomePower 2000 Plus】说明书-EN.pdf」,
  read-only bot download; 3,928,190 bytes, SHA-256 `e27d4db5606c140439dd32b7d17ab4ed428a62fbfbb5567c7664d8ac22032d51`
  (stored as `JHP-2000A-RC-US-en-V2.pdf`).
- 24 portrait pages, 368.79 × 524.69 pt, written by pypdf from the Illustrator master. No text layer and no fonts:
  all copy is outlined. App screenshots on pages 22–23 are embedded raster images.
- p1 cover (Model: JHP-2000A-RC, V2), p2 IMPORTANT, p3 paper table of contents, p4–p23 printed 01–20, p24 back cover.
- Field 查找引用: 「16-0102-000417 HTE26062000A-US-JAK 说明书A1 RoHS REACH Q.pdf」 (Illustrator 30.7, 45 artboard pages,
  33,695,004 bytes, SHA-256 `1be17195ea3a3135f28898edf18317fe4c835f09e01277756b9714d8f279571a`). Identity reference only;
  it is not stored in the package and no Web input is taken from it.

## Inventory searched

| Candidate root | What was compared |
| --- | --- |
| `data/manual_sources/JHP-3600A/US/git-20261012-541ca8a5-reviewed` (HomePower 3600 Plus, published reference) | every panel, LCD icon, button, symbol and App art; its PDF text layer for the transcription cross-check |
| `data/manual_sources/JHP-3000D`, `JHP-3600C`, `JHP-5000C` US | overview, LCD, operation, charging and App art |
| `docs/renderers/web/assets/shared/symbols/manifest.json` (76 variants) | all eleven safety symbols and the FCC mark, fixed 2% admission comparison |
| `docs/renderers/web/assets/shared/buttons/` | the four key-combination buttons |
| every `*lcd*` file under `data/manual_sources/` and `manual_sources/` (195 unique files) | inked-shape comparison of the 27 LCD description icons against this PDF's vector paths |

## Decisions (summary; per-file rows in `asset_decisions.json`)

| Slot | Decision | Reason | Background |
| --- | --- | --- | --- |
| overview, LCD map, operation, UPS, battery, charging panels | new complete panels | HomePower 2000 Plus chassis, port set, AC1/AC2 buttons and 26-position LCD differ from every HomePower reference | complete panel, leader lines and labels kept; body copy printed inside a panel is removed from the art and set as native text |
| in-box cards, sold-separately strip | new | this model's front and accessories | card art |
| App badges, QR, phone screenshots, control-panel diagram | new complete crops | screenshots name HomePower 2000 Plus; QR not assumed equal | badge pair / QR frame / phone frames kept |
| 14 LCD icons (Wi-Fi, Bluetooth, quiet charging, charging plan, self-powered, AC power, input, charge time, battery power, low battery, percentage, fault code, output, discharge time) | reuse existing files byte-identical | ≤ 0.02 mean difference against this PDF's paths | transparent |
| 13 LCD icons (TOU, UPS, output voltage/frequency, AC wall, car, solar, battery saving, charging power limit, discharge timer, connected batteries, energy saving, high/low temperature) | native vector extraction | closest existing file 0.05–0.30 mean difference | transparent, PDF paths only |
| POWER and DC/USB buttons | reuse `shared/buttons` power.svg, dc_usb.svg | same face and marking | transparent |
| AC 1 and LIGHT buttons | native vector extraction | shared `button/ac` prints AC (not AC 1); shared `button/led` has no bulb mark | transparent |
| eleven safety symbols, FCC mark | reuse existing shared catalog variants | each passes the fixed 2% admission; no catalog file added | transparent |

No body text or table is an image: all copy is native HTML from `transcription.json`.
