# JBP-1000B-SIL / US / English LCD line-break candidate

Status: pending operator review; publication_eligible=false. This candidate inherits no merge/publication authority or previous source acceptance.

The parent is `../git-20261008-7afcb2a1`, whose complete 52-page `Jackery Battery Pack-1.pdf` remains authoritative (SHA-256 `7afcb2a1e9e7b2011ddbfbe3ed81aa6c5ec5d196e4d9ad008208195fa06b6137`). English uses its existing native pages and component flow. All 50 original artwork files and the source geometry stylesheet are reused byte-identically; there is no extraction or new styling.

Only LCD row 6 (DC Input) changes: one `<br />` precedes the existing `Off:` label. Native text, values, other cells and other languages remain unchanged in the parent. The English-only derivative records current shared-input pins and keeps the prior package immutable.

Rebuild with Python 3.12 and `requirements.lock`, from the repository root:

```sh
python data/manual_sources/JBP-1000B-SIL/US/git-20261110-7afcb2a1-lcd-linebreak/rebuild.py --output /tmp/jbp1000bsil-lcd-replay --language en
python -m sphinx -W --keep-going -b html /tmp/jbp1000bsil-lcd-replay /tmp/jbp1000bsil-lcd-html
```

The pending candidate is prepared for review, with no live-table write or publication. Source text coverage/provenance is inherited; the previous desktop/mobile acceptance file is omitted.
