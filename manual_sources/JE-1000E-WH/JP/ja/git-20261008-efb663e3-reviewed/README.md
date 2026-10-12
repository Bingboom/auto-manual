# Jackery SlimPower H1 — JE-1000E-WH / JP / ja approved release

Operator instruction “上线提交发布”, 2026-10-08; MA-274, engineering PR #1461.
The [original candidate](../git-20261008-efb663e3/README.md) and its evidence remain unchanged.
`approval.json` binds the candidate commit, PDF, semantic copy, presentation and
independent shared-component requirements. The adapter checks these bindings
before building; approval removal, changed copy and altered components fail.

The 27-page Japanese PDF is the only textual authority. Filename V2.0/date are
provenance; printed version remains unknown. All 17 chapters, 60 artwork files,
620 checked native lines, native safety glyphs, source reading order and finished
localized panels retain the reviewed candidate. Four localized illustration
captions remain embedded with semantic companions. Warnings use shared callout
reflow; not every PDF warning-row frame/pictogram is reproduced.

From the repository root, rebuild into new directories:

```sh
PKG=manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-reviewed
PYTHONPATH=. python3 "$PKG/rebuild.py" --output /tmp/h1-reviewed-new
python3 -m sphinx -W --keep-going -b html /tmp/h1-reviewed-new /tmp/h1-reviewed-html-new
PYTHONPATH=. python3 "$PKG/verify.py" --html /tmp/h1-reviewed-html-new/manual.html
```

Follow-up edits require new operator review and refreshed approval bindings.
`seal.py` inventories source plus frozen MyST/assets. Generated file hashes are
excluded only from their own IR source envelope to avoid a hash cycle. The
complete committed source manifest remains the publication authority.

Publication follows the existing frozen-language receipt and Hello-Docs
`docs/publish/**` assembler. JP retains the existing regional component policy;
no EU policy exception or global asset-registry promotion is introduced. The
twelve reviewed native SVGs are byte-identical shared-catalog variants. Their
publication bindings check the original PDF, same-row caption pixels/text,
transparent margins and native glyphs through the existing symbol admission.
The supplied PDF is included unchanged for independent source reconstruction. Source
commit, engineering merge, mirror sync, publication merge, RTD receipt/resources
and live browser acceptance remain separately verified. No online table or queue
reads/writes; no `HTML_link` write. See the original candidate REVIEW for source
limits and the approved validation record for this release's actual results.
