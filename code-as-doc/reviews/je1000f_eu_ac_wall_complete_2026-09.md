# AC wall charging panel correction

Status: active

Source PDF p154 has a panel border ending at y=152.111pt. The frozen recipe clips
the shared artwork at y=136pt, cutting the bottom frame. Four locales share this
language-neutral asset. Recover the whole source panel with clip [26,52,340,153]
and the existing text-only redaction (preserve graphics/images); leave the native
paragraph below the image unchanged. Verify old retained pixels, full border at
12x, unchanged source/copy/all other images, four strict builds, cold IR replay,
publication scope and local/browser/RTD parity. New immutable frozen package;
no live asset registry, main recipe, renderer, CSS, source schema or translations
change. Engineering and docs/publish-only releases use existing authorization.

## Verification evidence

- Existing image: 1256 × 336 px. Complete export: 1256 × 404 px.
- Original source frame bottom is y=152.111pt; clip ends at 153pt.
- Both lower corners and the complete lower border verified at 12x.
- Retained upper area differs in only 24 antialias pixels, maximum channel
  delta 2/255; all source graphics are preserved. Caption text alone is removed.
- New PNG SHA-256: `b5775705d0545cc1a95826ff21841bc57ebd27617cdcbafbb0fa07e395bef276`.
- Four source extraction JSON files, all visible words and other 56 image assets
  per locale are exact. Full-book DOM changes only the AC image URL and the solar-direct container fill.
- Four strict Sphinx builds and byte-exact source-free IR replay passed.
- Formal intake, exact RTD build, publication scope and browser checks are
  recorded before opening the PR. Online acceptance follows both gated merges.

Historical recipe and frozen packages remain unchanged. The corrective recipe
is package-only/quarantined, not promoted into the live asset registry. MA-201
covers the bounded frozen-Web repair and publication. No renderer or CSS changes.

## Solar panel boundary and reuse audit

The solar-direct PNG already contains a rounded gray panel with a white top
margin. The shared component also painted a gray container behind it, exposing
two gray side strips above the source panel. Set only this figure binding
`panel_fill` to white; retain every source-image byte, native SolarSaga label,
and shared renderer/CSS. Desktop and narrow-browser checks cover the result.

The four added locales already share one frozen solar-direct artwork hash.
The existing five-language finished panels are not interchangeable whole:
English has UK socket artwork while DE/ES/IT have a different front socket
face. Panel/lead artwork is a cross-language reuse candidate, but the station
and port insets are model/region-bound. Do not claim nine identical whole-image
bindings or replace other products with this model-specific diagram. Nine-
language/cross-product layer migration remains separate from this bounded fix.

## Completed local acceptance

- `python3 -m unittest tests.test_asset_recipe tests.test_frozen_pdf_web`: 45 passed.
- `python3 build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2 --staging-root /tmp/ac-wall-complete-us-check --skip-root-index`: passed.
- Four strict Sphinx builds, exact RTD portal build and source-free IR replay passed.
- Publication audit: 58 targets retained; 54 unrelated target metadata records
  and 3,775 non-target files unchanged; 4,060 manifest files and 2,252 pool
  references verified. Original five locales remain at version 2.7.
- Actual browser at desktop and 390px: complete AC frame/corners, solar side
  strips absent, native captions visible and within the content width.
- AC source asset SHA matches the formal intake output exactly.
