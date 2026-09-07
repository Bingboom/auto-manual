# JS-100I EU English Web release readiness — 2026-09-06

Status: Git-traceable V2.0 Web package built and accepted locally from final
engineering main. It is ready for the shared Hello-Docs `docs/publish/**`
candidate. No online Base write, queue dispatch, Hello-Docs engineering edit,
or production publication occurred in this target task.

## Release identity

| Field | Value |
| --- | --- |
| Target | `JS-100I / EU / en` |
| Product | Jackery SolarSaga 100 Air |
| Version basis | Published manual `V2.0-2026-04-01`; release version `2.0` |
| Engineering implementation base | `9b356ecadfe355aae0eb474ef4c49bf168a01e4c` |
| Frozen-source Git ref | `50bdf3f56f72dac49f5489a9f69b93a4952fba94` |
| Config | `configs/config.solar-eu-en.yaml` |
| Structured copy | `docs/templates/page_solar/en/` |
| Frozen structured-data input | `data/manual_sources/JS-100I/EU/en/2.0/phase2/` |
| Structured-data snapshot SHA-256 | `190b63b33cc0c86002ad6d88dd8e7ca88962ee8350f8050c1e5748cc67ac515c` |
| Published PDF SHA-256 | `cec27af653d9f5da11d641e2431ddc0b71ced186bbadfd9594fa8cd9c96e1596` |
| Illustrator master SHA-256 | `5d7ded6ba7810505cfb4c91b128a71cbef16a0e11aae720cdbd887559224b96a` |
| Asset recipe SHA-256 | `45755c66d4d98ec356d120b5dd14a535b9633c17191e90de0285fd1bb8910c14` |
| Illustration manifest SHA-256 | `d2d63eac57d98272c6367a133b82a22d7831ce0d263867e458b79b039f700e52` |

The current published V2.0 English manual is the content authority: its English
body is physical pages 4–12. The Git-tracked `data/manual_sources` snapshot is
the actual build input for this release and was validated against that
authority. Its five CSV hashes and aggregate snapshot hash are pinned by
`source_manifest.json`; this does not claim that any online source was
synchronized.

## Frozen target package

The target handoff produced the exact release-root contract consumed by
`tools/publish_branch_assembly.py`:

```text
<release-root>/
└── JS-100I/EU/en/
    ├── latest/web/publish_meta.json
    └── versions/2.0/web/
        ├── md/
        │   ├── conf.py
        │   ├── index.md
        │   ├── manual_js100i_eu_en.md
        │   ├── _static/web_manual.css
        │   └── assets/ir/<sha256>/<13 semantic images>
        ├── html/index.html
        └── release_input_manifest.json
```

Local handoff for this run:

```text
/tmp/auto-manual-web-release-js100i-formal-20260906.qvYe7v/releases
```

The release metadata uses schema `auto-manual-web-publish/v1`, identifies
version `2.0`, carries the frozen-source Git ref above, points only inside
the release root, and has an empty `queue_record_ids` array.

Frozen output hashes:

| Artifact | SHA-256 |
| --- | --- |
| `manual_js100i_eu_en.md` | `5126285d0a34d91786ed7fe7084d376d7994cee2891946874e025fc12ef50dc9` |
| `manual.ir.json` | `eaa6cef4d8ca3da47dbd352b5033340d38ab5a9a225a488a57b408e22a1c5732` |
| verification `html/index.html` | `ec4235f26d910abdd9a47cd62fc1a789e1d77bd93a16677a1884936c128a9780` |
| verification nested manual HTML | `b611d2ba657a7d04330760a30c0d954d89fcd42c4d5e7c3acbc49ff8f38717e4` |

The package retains all 13 localized full-image illustrations with their
English in-figure annotations. It does not contain PDF, DOCX, IDML, AI, ZIP,
LaTeX, or other print/source artifacts.

## Acceptance results

| Gate | Result |
| --- | --- |
| Target tests | 8/8 passed, including formal source-manifest hash pins |
| Composition | 9 pages; Safety Tips first; five-card Inbox |
| Semantics | STC/BNPI notes retained; no LCD/UPS/App chapters |
| IR replay | Cold replay passed with `.rst`/`.csv` reads denied |
| Asset integrity | Tampered image rejected; 13/13 refs packaged |
| Direct target Sphinx | Sphinx 8.2.3 `-W` passed |
| Shared assembler | 1 target, route `JS-100I/EU/md`, 51 files inventoried |
| Assembled candidate Sphinx | Sphinx 8.2.3 `-W` passed |
| Candidate assets | 13/13 present; no forbidden print/source file |
| Root alias | `manual_js100i_eu_en.html` → canonical nested route |

The earlier direct-target browser run passed at 1440×900 and 375×812 with all
13 images loaded, zero image/page overflow, and five/one Inbox columns. The
assembled candidate uses byte-identical manual Markdown and assets and passed
the strict Sphinx rebuild. A second visual browser launch was unavailable only
because the Mac was locked; the shared publishing task can repeat that visual
check on the combined candidate before opening its PR.

Commands used for the formal Git-only handoff:

```bash
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.solar-eu-en.yaml \
  --model JS-100I --region EU --lang en \
  --data-root data/manual_sources/JS-100I/EU/en/2.0/phase2 \
  --staging-root <build-stage>
python tools/readthedocs_source.py \
  --build-root <build-stage>/docs/_build \
  --output-dir <build-stage>/docs/_build/rtd \
  --title "Jackery SolarSaga 100 Air User Manual"
python -m sphinx -W -b html \
  <build-stage>/docs/_build/rtd <build-stage>/html
python tools/publish_branch_assembly.py \
  --releases-root /tmp/auto-manual-web-release-js100i-formal-20260906.qvYe7v/releases \
  --output-dir <independent-candidate>/docs/publish \
  --title "Hello Docs Manual Library"
python -m sphinx -W -b html \
  <independent-candidate>/docs/publish/web <independent-candidate>/rtd-html
```

The target-only assembled candidate for this run is:

```text
/tmp/hello-docs-js100i-formal-candidate-20260906.MpB3qm/docs/publish
```

Its `publish_manifest.json` SHA-256 is
`4bb8aebbbc4dfd49e3ea2f94cc3afd89aa8c87d344b4377cbe2c7eebe7dda907`.
The centralized publisher should use the release root, not this target-only
candidate, so it can preserve existing Hello-Docs targets while assembling the
shared range.

## Formal publication route

The shared publishing task should run the same assembler against an independent
candidate seeded with the current Hello-Docs `docs/publish/**` tree. The
assembler stages this target under:

```text
docs/publish/sources/web/JS-100I/EU/md/
docs/publish/web/JS-100I/EU/md/
docs/publish/web/manual_js100i_eu_en.md
```

After a `docs/publish/**`-only PR is reviewed and merged into Hello-Docs main,
`.readthedocs.yaml` builds `docs/publish/web/`. The expected public alias is:

```text
https://ht-doc.readthedocs.io/manual_js100i_eu_en.html
```

Formal completion requires that real URL to return the intended V2.0 manual
after the Hello-Docs merge. Empty online association fields are not a blocker
for this Git-only release.

## Deferred online normalization

The read-only gap audit in
`reports/source_intake/JS-100I_EU/formal_business_input_*` is retained only as
optional future normalization context. It is not an approval request, release
dependency, or instruction to write online data in this batch. The current
batch explicitly performs no online Bitable or build-queue writes.
