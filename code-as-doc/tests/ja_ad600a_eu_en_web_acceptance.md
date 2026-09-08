# JA-AD600A / EU / en Web acceptance

## Target result

- Nine Web source pages: disclaimer, specifications, dimensions, inbox, overview, safety, FAQ, installation, and warranty.
- Sixteen source-derived images; no whole-page screenshot.
- Nine responsive inbox cards.
- Five governed installation figures, all reported as `finished-panel` with zero editable fallback and zero missing slots.
- One native specification composition, two warning callouts, and a six-section warranty with a 2-year badge.
- No LCD, UPS, or App content.

## Reproduction commands

```bash
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off python build.py check \
  --config configs/config.charger-eu-en.yaml \
  --model JA-AD600A --region EU --lang en \
  --data-root data/manual_sources/ja_ad600a_eu_en

AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off \
AUTO_MANUAL_PRESENTATION_PROFILE=web \
python build.py md \
  --config configs/config.charger-eu-en.yaml \
  --model JA-AD600A --region EU --lang en \
  --data-root data/manual_sources/ja_ad600a_eu_en \
  --staging-root /tmp/ja-ad600a-web

sphinx-build -W -b html \
  /tmp/ja-ad600a-web/docs/_build/JA-AD600A/EU/en/md \
  /tmp/ja-ad600a-web/docs/_build/JA-AD600A/EU/en/html

python -m unittest \
  tests.test_ja_ad600a_eu_en_target \
  tests.test_ja_ad01a_eu_en_target
```

## Recorded local evidence

- `build.py check`: passed with `AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off`.
- Real Pandoc Web build: passed.
- Sphinx 8.2.3 `-W`: passed with zero warnings.
- Target regressions: 15 tests passed, including source-snapshot identity and tamper rejection.
- Repository unit suite: 3,864 tests passed; 22 skipped.
- Browser visual QA: desktop and 375 × 812 mobile views passed. Inbox cards reflow from multiple columns to one column; installation figures retain complete gray frames and labels; the 2-year warranty badge and cards remain readable; no broken images or horizontal crop was observed.
- Local preview route: `http://127.0.0.1:18821/manual_jaad600a_eu_en.html` while the documented local server is running.

## Evidence boundary

This acceptance proves local source, build, IR replay, hash, and responsive rendering behavior only. It is not evidence of merge, formal publication, or live-system update.
