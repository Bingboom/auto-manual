# SlimPower H1 JP — Web edition without printed cover

Operator instruction: “封面 不要放进去网页版里面啊”, continuing “上线提交发布”, 2026-10-08, MA-277.
The [previous approved edition](../git-20261008-efb663e3-reviewed/README.md) and original candidate remain immutable.

The Web starts at **安全上のご注意**. The complete printed-cover chapter is omitted from the Web flow;
its PDF and semantic source remain archived in `source/print-cover.json`. All 16 subsequent chapters
retain their exact previously approved blocks, technical/legal wording and original artwork bytes.
`source/cover-removal.json` binds that comparison. The source manifest explicitly records the Web exclusion;
`approval.json` binds the new chapter map, component counts, styles and unchanged body digest.
Printed version remains unknown; this technical snapshot is a Web edition, not a paper-version change.

From repository root:

```sh
PKG=manual_sources/JE-1000E-WH/JP/ja/git-20261008-efb663e3-no-cover-reviewed
PYTHONPATH=. python3 "$PKG/rebuild.py" --output /tmp/h1-no-cover-cold
python3 -m sphinx -W --keep-going -b html /tmp/h1-no-cover-cold /tmp/h1-no-cover-html
PYTHONPATH=. python3 "$PKG/verify.py" --html /tmp/h1-no-cover-html/manual.html
```

The existing shared Manual IR / ComponentSpec renderers own output. JP admission, native safety symbols,
App frames, source glyph recoveries and original source anomalies retain the prior edition's boundaries.
The integrated CSS asset-pooling repair is auto-manual #1463. A fresh Git-only single-language receipt,
publish-only Hello-Docs PR, exact RTD/resources and live desktop/mobile acceptance are required.
No live tables, queue, source schema, HTML_link or asset-registry writes.
