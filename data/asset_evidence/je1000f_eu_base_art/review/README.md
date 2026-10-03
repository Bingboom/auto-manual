# JE-1000F/EU Operation base-art candidates

These six exports are **quarantined review candidates**. They are not registered, bound to a Web target, or approved for publication. The source is `Jackery Explorer 1000 User Manual (JE-1000F) V2.0 EU-UK-2026-06-18.pdf`, SHA-256 `0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe`. Page numbers below are physical PDF pages. The recipe is `data/asset_recipes/manual_je1000f_eu_base_art_pilot.json`.

Open the [English contact sheet](en_contact.png) and [German contact sheet](de_contact.png) for source-left/candidate-right comparisons. The individual pair images below are at 4× and the candidate close-ups are rendered directly from each candidate PDF at 12×.

| Candidate | Source page | Candidate PNG SHA-256 | Review images | Intended removal / protected artwork |
| --- | ---: | --- | --- | --- |
| `main_power_en` | 11 | `a94db05b2cccb32a68aef15a83aa1b0850d4be654ee97071eb1ddedccfe9b01e` | [pair](main_power_en_pair.png) · [12×](main_power_en_12x.png) | Remove clipped fixed standby box and unrelated callout continuation; preserve UK outlet holes, product print, button, finger. |
| `ac_output_en` | 11 | `42b3c81616e00de18fc4be2a08f9eb6ed1c9be9a214a01d3388d281c27caf677` | [pair](ac_output_en_pair.png) · [12×](ac_output_en_12x.png) | Remove On/Off step words, bracket, old step leaders; preserve UK outlet and device/appliance lines. |
| `dc_usb_output_en` | 12 | `2bbdfd064ffbffaf79f642ad9f7940f9bea9640efb17ceab01d085e18d68fc7a` | [pair](dc_usb_output_en_pair.png) · [12×](dc_usb_output_en_12x.png) | Remove On/Off step words, bracket, old step leaders; preserve upper finger, USB connectors, lower DC circle. |
| `main_power_de` | 63 | `477a0acebd7320f67945a7021f1304b4de957cf54e4bdba693b2cd4b4874802b` | [pair](main_power_de_pair.png) · [12×](main_power_de_12x.png) | Remove clipped fixed standby box and unrelated callout continuation; preserve German outlet faces, product print, button, finger. |
| `ac_output_de` | 63 | `ebfa352dcc8b89cec6c6b483ef3f12695e04336bbbc1c222a04d0f97bcf9c3a7` | [pair](ac_output_de_pair.png) · [12×](ac_output_de_12x.png) | Remove Ein/Aus step words, bracket, old step leaders; preserve Schuko socket holes and appliance lines. |
| `dc_usb_output_de` | 64 | `45d29667382a39696259df1547e963f5ebc11b642c32785bc46b312dc6152644` | [pair](dc_usb_output_de_pair.png) · [12×](dc_usb_output_de_12x.png) | Remove Ein/Aus step words, bracket, old step leaders; preserve upper finger, USB connectors, lower DC circle. |

## Inspection and gate

The 12× views were inspected for complete hands, device contours, buttons, UK and Schuko socket geometry, USB plugs, and the lower DC circles. The 4× source/candidate pairs show that the fixed step words, bracket, and standby box are absent. `POWER`, `AC`, `DC/USB`, brand and port labels are fixed labels in the source drawing and deliberately remain. Their presence is not translated copy.

All 12 committed PDF/PNG files were SHA-256 compared with the official intake's `/tmp/je1000f-eu-base-art/manifest.json` and packaged files; all match. The pairs compare independently rendered source-page crops and candidate PDFs; color/antialias bytes can differ, so visual review of the shapes is the approval gate. The operator still needs to confirm each candidate by pixels before any registry enrollment or target binding.

The isolated [EN](flow_preview/en.html) and [DE](flow_preview/de.html) flow previews use the actual review RST and the shared renderer at commit `d6b65465f113fa09db5a1470d7803107f064e4d2`. Each preview has two steps in each of three slots, three main-power supporting lines, one AC prerequisite and one DC/USB prerequisite. The fourth 12-hour line stays after Main power, outside the figure. The IEC/EN/UL 62368-1 caution stays after DC/USB, outside the figure. Each appears once in the delivered HTML. The preview references the local quarantine PNGs; it is not a target binding. Browser visual acceptance through CUA remains pending because the browser entry timed out.

The [candidate target overlay](flow_preview/target_overlay_candidate.json) is review evidence only. It retains all 11 required slots and the five existing coverage locales, grants only the three pilot slots, and maps EN/DE to their distinct candidate PNG hashes. A temporary copy of A's contract stack resolved this object successfully; the formal `target_overlays.json` was not changed.
