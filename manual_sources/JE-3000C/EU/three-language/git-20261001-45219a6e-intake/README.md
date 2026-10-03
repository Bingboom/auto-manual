# JE-3000C EU Portuguese, Dutch and Polish intake

Source: `HTE156-EU-9国语言-0923.ai`, 152 PDF-compatible pages, SHA-256
`45219a6e488358c4a76b847cd0288f5a865fd8ab899d8ceb9e154a5696816574`.
Native text is extracted directly; OCR is not used. Bodies are pt 104–119,
nl 120–135 and pl 136–151. Page 4 provides preface content, page 7's print
contents are omitted, and page 152 supplies the shared legal back matter.
The technical package version does not assert a printed-manual revision.

`source/target_layout.json` supplies target-local geometry and explicit
shared-component bindings. `artwork/reuse-review.json` records inspected
candidates, reuse choices, source/hash and background policy. The three
`*_assets_manifest.json` files bind those bytes. `extraction_recipes/native-artwork.json`
reproduces the 16 artwork extracts using the existing asset pipeline.

To rebuild one candidate from the repository root, substitute the source AI
path and an empty output directory; repeat with `pt`, `nl` or `pl`:

```sh
python3 -m tools.web.frozen_pdf_web \
  --pdf '/path/to/HTE156-EU-9国语言-0923.ai' \
  --recipe-root manual_sources/JE-3000C/EU/three-language/git-20261001-45219a6e-intake \
  --assets-manifest manual_sources/JE-3000C/EU/three-language/git-20261001-45219a6e-intake/pt_assets_manifest.json \
  --output /tmp/je3000c-pt-candidate --language pt
python3 -m sphinx -W -b html /tmp/je3000c-pt-candidate /tmp/je3000c-pt-html
```

The adjacent `git-20261001-45219a6e-native-web` package contains the reviewed
frozen output. Its IR can replay through `tools.web.frozen_ai_web.replay_package`
without opening the original AI or rereading this intake.

Ordinary artwork is textless, with native labels and CSS text containers.
Preserve device/connection geometry and outer panels; removing text alone
must not leave empty caption boxes. Dense overview callouts and real App UI
remain source artwork. Shared symbols must stay byte-identical to their
recorded source. No per-language CSS or alternate renderer is introduced.

Dutch remains in source review: AC/DC labels and combined car-input current
need an operator decision. `source/errata.json` contains no unapproved fixes;
the frozen Dutch IR is explicitly not publication eligible. Existing six
language editions remain on their original source authority.
