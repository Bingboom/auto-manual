# Layout Params Change Log Template

Updated: 2026-03-12

Use this template to record each meaningful [`data/layout_params.csv`](../../data/layout_params.csv) adjustment.

---

## 1. Change Metadata

- Date:
- Author:
- Branch:
- Related task:
- Affected family:
  - [`configs/config.us.yaml`](../../configs/config.us.yaml)
  - [`configs/config.ja.yaml`](../../configs/config.ja.yaml)
- Affected target examples:
  - `JE-1000F / US`
  - `JE-1000F / JP`
- Goal in one sentence:

---

## 2. Parameter Changes

| key | old value | new value | unit | affected area | reason |
| --- | --- | --- | --- | --- | --- |
| `comp_spec_section_after` | `0.40` | `0.20` | `mm` | `spec` | tighten section gap |

---

## 3. Related Code Changes

Only fill this section if `.tex` or Python files also changed.

| file | location | summary | should be parameterized later |
| --- | --- | --- | --- |
| [`docs/renderers/latex/components_spec.tex`](../../docs/renderers/latex/components_spec.tex) | `Lxx` | example note | `yes/no` |

---

## 4. Verification Commands

```powershell
python build.py validate --config configs/config.us.yaml
python build.py pdf --config configs/config.us.yaml --model JE-1000F --region US
```

If JP is affected:

```powershell
python build.py pdf --config configs/config.ja.yaml --model JE-1000F --region JP
```

Optional clean rebuild:

```powershell
python build.py clean --config configs/config.us.yaml
python build.py pdf --config configs/config.us.yaml --model JE-1000F --region US
```

---

## 5. Verification Result

- Validation:
- Build result:
- Output path:
  - [`docs/_build/<model>/<region>/pdf/manual_{model_slug}_{region_slug}.pdf`](../../docs/_build)
- Pages compared:
- Conclusion:

---

## 6. Risk and Rollback

- Known side effects:
- Rollback method:
  - revert CSV keys:
  - or revert commit:

---

## 7. Reviewer

- Reviewer:
- Review result:
- Final confirmation time:

