# JA-CA3SA / EU / en Web acceptance

## Target result

- Three native Web source pages: port functions, connection operation and examples, and caution/prohibited connections.
- Ten complete labeled diagram crops regenerated from the Git-frozen PDF-compatible Illustrator source; no whole manual page is rasterized.
- Physical English pages 4-7 are represented once. Physical page 8 is recorded as a duplicate production summary artboard and is excluded.
- One native caution callout and ten responsive finished-panel images.
- No specification chapter, Inbox, LCD, UPS, App chapter, warranty period, or legal tail because the designated source contains none of them.

## Source and traceability checklist

- [x] Source target is JA-CA3SA / EU / en and DingTalk record `tQDWZr68hK`.
- [x] Source SHA-256 is `88f1fa0dd86fd8e7457b50942be52e2a558acecaf5f9bc70edc9f7dbecd311ab`.
- [x] The exact 2,890,471-byte AI source is frozen under `manual_sources/JA-CA3SA/EU/en/git-20260909-88f1fa0d/source/`.
- [x] The six-file local data snapshot, Product Manual Plan, resolved manifest, structured copy, recipe, asset registry entries, and illustration manifest are committed inputs.
- [x] The asset recipe replays without network access and verifies all ten output hashes.
- [x] No online Base, publication queue, OSS location, or release branch is written.

## Content checklist

- [x] Port diagram retains DC8020 male/female labels, the change-over switch label, leader lines, and Jackery product marking.
- [x] Two-panel and three-panel operating diagrams retain the original device labels.
- [x] Examples 1-4 retain their complete connection topology and labels.
- [x] All three prohibited connections retain their cross marks, complete gray frames, panel counts, and power-station labels.
- [x] Switch states remain explicit: two panels use OFF; ON requires three panels connected at the same time.
- [x] Native prose is not duplicated below the connection panels; images own their embedded device and count labels.

## Reproduction commands

```bash
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off python build.py check \
  --config configs/config.charger-eu-en.yaml \
  --model JA-CA3SA --region EU --lang en \
  --data-root data/manual_sources/ja_ca3sa_eu_en

AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.charger-eu-en.yaml \
  --model JA-CA3SA --region EU --lang en \
  --data-root data/manual_sources/ja_ca3sa_eu_en \
  --staging-root /tmp/ja-ca3sa-web

sphinx-build -W -b html \
  /tmp/ja-ca3sa-web/docs/_build/JA-CA3SA/EU/en/md \
  /tmp/ja-ca3sa-web/docs/_build/JA-CA3SA/EU/en/html

python -m unittest \
  tests.test_ja_ca3sa_eu_en_target \
  tests.test_ja_ad01a_eu_en_target \
  tests.test_ja_ad600a_eu_en_target
```

## Recorded local evidence

- `build.py check`: passed with `AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off` and no capability warning after the explicit accessory exemption was registered.
- Real Pandoc Web build: passed and produced a three-page whole-document IR package.
- Sphinx 8.2.3 `-W`: passed with zero warnings.
- Target and adjacent charger/accessory regressions: 73 tests passed in the focused run.
- Full repository regression: 3,912 tests passed; 22 tests skipped by existing conditions.
- Browser visual QA: 1440 px desktop and 390 px mobile views passed. All ten illustrations remain within the content column; labels and gray frames are intact; the caution callout remains readable; no broken image or horizontal crop was observed.
- Local preview route: `http://127.0.0.1:18831/manual_jaca3sa_eu_en.html` while the documented local server is running.

## Evidence boundary

This acceptance proves the Git-frozen source, local build, IR replay, hash, and responsive rendering behavior only. It is not evidence of merge, formal publication, OSS upload, or live-system update.
