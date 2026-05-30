# Review Preview Site

This directory is the static-site packaging root for review-stage HTML sharing.

Generated output:

- `dist/`

The generated site is built by:

```powershell
python tools/process_docs/build_review_preview.py --config configs/config.us.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

Do not hand-edit `dist/`.
It is generated from:

- review HTML under `docs/_build/<model>/<family>/<lang>/html/` or `docs/_build/<model>/<family>/html/`
- review Word under `docs/_build/<model>/<family>/<lang>/word/` or `docs/_build/<model>/<family>/word/`
- diff-report HTML / CSV under `reports/version_tracking/<model>/<family>/`
- metadata produced by `tools/process_docs/build_review_preview.py`

Expected packaged structure:

- `index.html`: workspace root
- `manual/`: grouped review HTML by family, model, and language
- `changes/`: family-level diff pages plus a compatibility redirect
- `downloads/`: family-scoped Word, workbook, and CSV exports
- `generated/`: metadata, changes, and workspace data
- `manual/index.html` and `changes/index.html`: compatibility redirects for the default workspace entry points

The generated `index.html` is meant to be the designer-facing entry page:

- start from the workspace root
- pick a family, model, and language
- then open the rendered manual or the shared family diff package
- use the Word / Excel downloads when you need an offline handoff
- use raw file-level diff links only when deeper maintainer tracing is needed

