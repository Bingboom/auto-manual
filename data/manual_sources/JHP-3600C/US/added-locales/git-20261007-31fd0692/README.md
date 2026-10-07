# JHP-3600C / US French and Spanish Web candidates

This Git-only extension inherits the published English structure from `../../en/git-20261005-31fd0692`. The same 97-page PDF remains authoritative; it is referenced, not duplicated. French uses physical pages 35–65, Spanish 66–96, with native p2 prefaces and shared p97 contact copy. `source_manifest.json` locks source inputs, consumed assets, shared repository contracts and frozen output hashes.

Each locale has 20 chapters and the same shared ComponentSpec inventory as English. Of 90 consumed assets, 86 are byte-identical approved English assets. Four panels use native source artwork: front overview, side overview, App buttons and complete App connection screenshots. The generic shared Explorer1000 App result screenshot differs from the native HomePower3600 Plus UI and is deliberately excluded from these two locale outputs. All eleven ReferenceFigures retain live editable native captions; blank caption frames remain CSS. Dense overview labels and App UI remain source-finished panels as in the accepted English content mode.

## Reproduce from the repository root

Use a new output directory for each replay:

```sh
python3 data/manual_sources/JHP-3600C/US/added-locales/git-20261007-31fd0692/rebuild.py --language fr --output tmp/jhp3600c-fr-replay
python3 data/manual_sources/JHP-3600C/US/added-locales/git-20261007-31fd0692/validate_source.py --language fr --output tmp/jhp3600c-fr-replay
python3 -m sphinx -W --keep-going -b html tmp/jhp3600c-fr-replay tmp/jhp3600c-fr-site
```

Replace `fr` with `es` for Spanish. The frozen `web/<locale>` folders are shared Manual IR, MyST, Sphinx scaffold, styles and assets, ready for the existing frozen-Web publication pipeline after review. This package does not enroll a phase2/print target or write a live queue, Base or HTML_link. The English merge authorization does not cover this new extension.

`source/<locale>/copy_bindings.json` records native selections. `native_exceptions.json` records per-node corrections where repeated English labels must bind to different native captions. `illustrative_copy_exceptions.json` admits only specific small labels remaining inside approved illustrative artwork. Repeated warning/tip labels introduced by PDF reading order are separated into their existing label slots and removed from body copy. Inherited `source_ref` values describe English blueprint geometry; `copy_bindings.json`, native pages and per-node exceptions provide native wording provenance. The validation script fails on other source-line omissions or asset hash changes. Its line coverage is a useful omission check, not proof of sentence placement; semantic mapping and source review remain necessary.

## Source differences retained for review

The native PDF has mixed-language and model inconsistencies. They are preserved rather than silently translated or corrected:

- FR p39 mentions HomePower3600 Plus; p53 mentions HomePower3600 Max and has an English solar charging heading. The UPS paragraph on p45 includes English, p49 EPO copy is English, and p57/p62 bypass specifications include English. The indoor-use signal is AVERTISSEMENT, the temperature warning uses only 130°C, and the low-power energy-saving note is absent. p63 battery-pack short-circuit caption and temperatures retain native English. p65 ATS package caption retains its unusual source reading order.
- ES p70 LCD heading and p71 self-powered label are French; p72 energy-saving description is French and battery text includes BateríaBatterie / encendido.allumé. The p73 hold instruction and p77 cable caption are French. p78 clearance uses pied, p80 backup heading and p81 cable notice are French, and p86 F8 action is French. p87/p93 main-station short-circuit label is French; p94 battery-pack caption is English. p83 signal is ATTENTION, p90 App signal is REMARQUE, p95 enclosure label is CONSEJOS. Native model spellings JBP-3600 A and JA-TS05 A are retained in their specification tables.
- Both native App result screens show HomePower3600 Plus. Complete phone frames and UI are retained. Small package covers, mounting-template print, ATS App / STEP labels and SolarSaga model labels stay illustrative in the inherited art.

No FR/ES merge or live publication is claimed by this candidate package.
