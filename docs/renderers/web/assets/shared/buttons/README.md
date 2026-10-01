# Shared button illustrations

These transparent SVGs retain the button paths from the existing approved
shared PDF assets. The source page and rectangular table backdrop are omitted;
the white circular button face, switch, indicator dot and product markings stay
intact. All lettering is outlined and needs no installed fonts.

| Semantic key | SVG | Product marking |
| --- | --- | --- |
| `button/power` | [power.svg](power.svg) | POWER |
| `button/ac` | [ac.svg](ac.svg) | AC |
| `button/dc_usb` | [dc_usb.svg](dc_usb.svg) | DC/USB |
| `button/led` | [led.svg](led.svg) | LIGHT |

[manifest.json](manifest.json) records source paths, source hashes, asset
hashes, selected path counts and the language-neutral scope. The original
approved PDF/PNG assets and their extraction recipe are unchanged.

Reuse the SVG by semantic key when the button shape and markings match. Keep
localized captions, combination signs and hold instructions in native HTML.
Copy the asset unchanged into each frozen Web bundle and verify its hash.

The JP local preview consumes these files. This asset addition does not update
the live Feishu registry or publish a manual.
