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
| `button/power-bottom` | [power-bottom.svg](power-bottom.svg) | POWER below switch |
| `button/usb-bottom` | [usb-bottom.svg](usb-bottom.svg) | USB below switch |
| `button/ac-bottom` | [ac-bottom.svg](ac-bottom.svg) | AC below switch |

The lower-marking variants preserve original JHP-3600C US PDF p13 paths and
are Git review candidates, without online registry promotion. Their source
boxes, drawing indices and hashes are recorded in the manifest and
`data/asset_recipes/manual_jhp3600c_us_native_buttons.json`. Upper and lower
markings are different artwork; USB and DC/USB are different product markings.
Select the matching variant after visual comparison, rather than substituting
the default solely because its semantic function matches.

[manifest.json](manifest.json) records source paths, source hashes, asset
hashes, selected path counts and the language-neutral scope. The original
approved PDF/PNG assets and their extraction recipe are unchanged.

Reuse the SVG by semantic key when the button shape and markings match. Keep
localized captions, combination signs and hold instructions in native HTML.
Copy the asset unchanged into each frozen Web bundle and verify its hash.

The JP local preview consumes these files. This asset addition does not update
the live Feishu registry or publish a manual.
