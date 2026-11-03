# JHP-1000A correction review — 2026-11-03

Local candidate checks passed. Publication and the Feishu checkbox remain pending.

- Source identity: current record reczz28SlRGJh40c attachment metadata matches the audit download; PDF SHA-256 cb256e64ddf9a998f4717e3ec2b038b9ef7711572f7d9b752667f1d6e64077c1.
- Page 8 / printed 05: all LCD numbers 1–25 and leader lines visible in the widened original crop. The only changed image is assets/lcd-map.png; old interior pixels are unchanged. One old right-edge raster column differs in clip antialiasing, documented in source-parity.json.
- Page 13 / printed 10: four native plus signs restored between the existing original button drawings. Visible text is otherwise identical; all image paths and alt text are unchanged.
- Existing model tests: 10/10 passed against the new package (including all 491 Web transcription lines, exact model facts, pinned inputs, seven symbol admissions, derived-content parity and cold replay). The historical edition separately passed 10/10 and remains unchanged.
- Strict Sphinx build: `python -m sphinx -n -W --keep-going -b html <rebuild-output> <html-output>` passed.
- Browser widths 1280, 1024, 390: all 64 images load, four plus signs visible, no uncontained table/image overflow. Desktop key table fits its frame (653/653 and 669/669 px); phone rightmost column is reachable by horizontal scrolling.

The existing suite is reusable without test edits: import `tests.test_jhp1000a_us_web`, set its PACKAGE to this revision, and run `unittest.defaultTestLoader.loadTestsFromModule(module)`. Browser and parity results are in the adjacent JSON files. Source concerns and approved print/Web exclusions remain as in the historical edition.


## Conditional release authority (2026-11-03)

Operator grant: 授权本批逐本全绿后合入上线. MA-381 records delegated sequential verification and conditional merge/publication authority. `source/approval.json` binds the exact source inputs. Approval metadata changed; rendered Markdown remains byte-identical to the locally verified v3 candidate. Online verification and Feishu checkbox remain pending.
