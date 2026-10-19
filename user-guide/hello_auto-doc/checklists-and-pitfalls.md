# Workflow guide: page contracts, pitfalls and verification checklist

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 10. Page Contracts

The repo now supports page contract checks under:

- [`docs/templates/contracts/03_product_overview.yaml`](../../docs/templates/contracts/03_product_overview.yaml)
- [`docs/templates/contracts/05_operation_guide.yaml`](../../docs/templates/contracts/05_operation_guide.yaml)
- [`docs/templates/contracts/12_app_setup.yaml`](../../docs/templates/contracts/12_app_setup.yaml)

Current scope:

- contracts are matched by source template path from `config.pages`
- `check` validates required placeholders, spec row keys, page-value selectors, and required assets
- `required_assets` accepts both existing path values and `asset:<asset_key>`; `check` and materialization share the same model/region/language-bound resolver, so semantic scope/status decisions cannot drift between the two stages
- current coverage includes `03_product_overview`, `05_operation_guide`, and `12_app_setup`
- the active US and JP template families can each declare their own required placeholder sets
- contracts can be scoped by `allowed_languages`, `allowed_regions`, and `allowed_models`

Current contract keys:

- `required_placeholders`
- `required_spec_keys`
- `required_page_values`
- `required_assets`
- `allowed_languages`
- `allowed_regions`
- `allowed_models`

Why this matters:

- a page can fail early when required page-value bindings are missing
- fallback values in [`conf_base.py`](../../docs/conf_base.py) no longer hide missing product-specific spec data
- new model onboarding becomes easier to validate before Word/PDF export

---

## 11. Common Pitfalls

### 11.1 Editing the wrong layer

Before review starts:

- edit template/data

After review starts:

- edit [`docs/_review/<model>/<region>/**`](../../docs/_review)

Never edit:

- [`docs/_build/<model>/<region>/rst/**`](../../docs/_build)

Use template/data only for shared reusable changes or intentional reseeding.

### 11.2 `?` appears in output

This is usually caused by dirty page-value rows in [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv), not by the template structure itself.

### 11.3 Old model names survive in the new manual

This usually means one of these happened:

- a template still contains hard-coded model text
- `product_name` in [`Spec_Master.csv`](../../data/phase2/Spec_Master.csv) was not updated
- the wrong `config`, `model`, or `region` was used

`check` now reports this as `STALE_IDENTITY_LITERAL`.
If a foreign model mention is intentional, add it to `checks.allowed_foreign_identity_literals` in the config.

### 11.4 Hard-coded title in config

If `build.word_title` is fixed to an old model name, the generated Word title will stay wrong even if `PRODUCT_NAME` is correct.
Prefer a placeholder-based title such as:

```yaml
word_title: "|PRODUCT_NAME| User Manual"
```

---

## 12. Verification Checklist

After changing templates or CSV values, verify at least the following:

1. `python build.py check --config ...` succeeds
2. `python build.py doctor --config ... --model ... --region ...` reports no blocking errors for the current Word/PDF path
3. the target bundle appears under [`docs/_build/<model>/<region>/rst/`](../../docs/_build)
4. the review bundle appears under [`docs/_review/<model>/<region>/`](../../docs/_review)
5. generated pages contain no unresolved placeholders such as `|PRODUCT_NAME|`
6. generated pages contain no stale model names from older products
7. safety and spec still resolve from the intended source, including the JP template-backed safety page and the remaining CSV-backed generated pages
8. the expected `.docx`, `.html`, or `.pdf` file is generated when requested
9. `publish` or `release-manifest` produced a JSON / CSV record under [`reports/releases/<model>/<region>/<lang>/manifests/<timestamp>.json|csv`](../../reports/releases); a versioned Publish also produced an immutable `versions/<version>/snapshot/release_snapshot_identity.json` and the manifest points to that archive
10. `python build.py release-rebuild-verify --manifest <manifest.json>` reports `status=passed` for the versioned release on its recorded toolchain

Useful checks:

```powershell
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\|[A-Z0-9_]+\|'
Select-String -Path docs\_build\JE-1000F\US\rst\page\*.rst -Pattern '\?'
git status --short -- docs/_review/JE-1000F/US
```

---

## 13. One-Sentence Rule

Templates and CSV create the first draft.
[`docs/_review/**`](../../docs/_review) becomes the target editing source after review starts.
[`docs/_build/**/**/rst/**`](../../docs/_build) remains the runtime publish bundle behind the final outputs.
