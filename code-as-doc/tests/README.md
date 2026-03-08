# Tests

Run all tests:

```bash
python3 -m unittest discover -s tests -v
```

Notes:

- Current tests are all hard assertions and should pass.
- If new known issues are intentionally tracked before fix, use `@unittest.expectedFailure` temporarily and remove it after remediation.

## Build Smoke (Word)

JA template to Word (`page_ja`) smoke:

```bash
python3 tools/gen_index_bundle.py --config config.ja.yaml --model JE-2000F --region JP
python3 tools/word_bundle.py --config config.ja.yaml --model JE-2000F --region JP --output manual_demo_ja.docx
```

Expected output:

- `docs/_build/word/manual_demo_ja.docx`

Note:

- When using `tools/build_docs.py` for JA full chain, ensure `build.output_pdf` matches the actual generated LaTeX PDF filename.
