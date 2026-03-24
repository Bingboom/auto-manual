# Review Preview Site

This directory is the static-site packaging root for review-stage HTML sharing.

Generated output:

- `dist/`

The generated site is built by:

```powershell
python tools/process_docs/build_review_preview.py --config config.yaml --model JE-1000F --region US --source review --from-ref HEAD~1 --to-ref HEAD
```

When Vercel hosting is enabled for design sharing, GitHub Actions should:

- run the command above
- convert `dist/` into `.vercel/output/static`
- deploy the static result with `vercel deploy --prebuilt`

Do not hand-edit `dist/`.
It is generated from:

- review HTML under `docs/_build/<model>/<region>/html/`
- diff-report HTML under `reports/version_tracking/<model>/<region>/`
- metadata produced by `tools/process_docs/build_review_preview.py`
