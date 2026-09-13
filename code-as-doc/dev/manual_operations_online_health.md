# OPS-05b1: bounded read-only HTTP checks

Discovery: OPS-05a checks local release artifacts, not deployed links. The RTD
portal already owns frozen index discovery and OPS-02 validates stored identity;
reuse that catalog rather than inventing a second inventory or live data table.

Plan: validate the complete frozen URL inventory before networking, then perform
bounded HTTPS HEAD checks with same-origin redirects only. Report HTTP accessibility
separately from exact deployment identity, translation completeness, visitor metrics
and ownership, which remain `no_data`. No workflow, online-table write, feedback
submission, scheduler or service is introduced.

Safety net: URL/redirect tests, legacy language uncertainty, empty inventory,
request limits and HTTP failure tests, full suite, and a read-only live run against
the existing RTD site. Code rollback is an independent PR; reports are disposable
derived files, never content authority.

## Running a check

Run against the existing frozen publish source (with its sibling metadata), not
an HTML output directory. Example in the business mirror checkout:

```bash
python -m tools.manual_operations_online_health \
  --web-root docs/publish/web \
  --base-url https://ht-doc.readthedocs.io/ \
  --max-publications 100 \
  --output reports/manual_operations_health/http.json
```

The cap defaults to 100 publications (explicitly adjustable up to 1000); each
request has a 10-second timeout. Redirects must stay HTTPS on the same origin
and may not add credentials, query strings or fragments. URLs come only from
the frozen index; planned languages never generate guessed requests. Empty
inventory reports `no_data`, not zero failures. A failed HTTP check exits 1.

HTTP success does **not** prove manual body correctness, asset availability,
absence of a soft-404, the deployed commit/version, or complete translations.
The report names these limits and leaves deployment identity, full translation
coverage, ownership and visitor metrics `no_data`. Combine it with
[local artifact checks](manual_operations_health_report.md), not a second copy
of body content. No new service, scheduled job or online-table write is created.

Live read-only evidence (2026-09-13 08:35 UTC): the existing 21-publication frozen
index produced 21 successful HEAD checks against RTD, zero HTTP failures. This
does not close OPS-05 ownership/cadence or OPS-07 end-to-end acceptance.
