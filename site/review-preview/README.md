# Review Preview Site

This directory is the static-site packaging root for review-stage HTML sharing.

Generated output:

- `dist/`

The generated site is built by:

```powershell
python tools/process_docs/build_review_preview.py --config config.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

Do not hand-edit `dist/`.
It is generated from:

- review HTML under `docs/_build/<model>/<region>/html/`
- review Word under `docs/_build/<model>/<region>/word/`
- diff-report HTML / CSV under `reports/version_tracking/<model>/<region>/`
- metadata produced by `tools/process_docs/build_review_preview.py`

Expected packaged structure:

- `manual/`
- `changes/`
- `downloads/`
- `generated/`

The generated `index.html` is meant to be the designer-facing entry page:

- start from the rendered manual
- then open the change report shortcuts
- use the Word / Excel downloads when you need an offline handoff
- use raw file-level diff links only when deeper maintainer tracing is needed
