# Publish XeLaTeX apt-cache acceptance — 2026-07-31

## Scope

This record covers Workstream W Stage 4a item 1: cache the downloaded apt
archives for the XeLaTeX/CJK package set used by the remote Publish queue.
Both runs used PR #817 commit `6823150b` and
`texlive_smoke_only=true`, which skips `process-build-queue` and therefore
does not select, claim, build, or write back any Feishu queue row.

The smoke path fixes `SOURCE_DATE_EPOCH`, compiles the same minimal XeLaTeX
document, and reports the PDF SHA-256 in the Actions summary.

## Cold and warm runs

| Run | Cache | XeLaTeX install | Job total | Smoke PDF SHA-256 |
| --- | --- | ---: | ---: | --- |
| [30641593186](https://github.com/Bingboom/auto-manual/actions/runs/30641593186) | miss, saved successfully | 153 s | 3m33s | `5585de342f8441a7e0345316973f44485de198d2dabac87f4b9f7ccafe7c6ffd` |
| [30641927768](https://github.com/Bingboom/auto-manual/actions/runs/30641927768) | hit | 127 s | 3m01s | `5585de342f8441a7e0345316973f44485de198d2dabac87f4b9f7ccafe7c6ffd` |

The warm archive cache reduced the measured install step by 26 seconds
(approximately 17%) and the whole smoke job by 32 seconds. The SHA-256 values
match exactly.

An earlier exploratory cold run exposed root-owned apt `partial/lock` entries
that made `actions/cache` warn instead of saving. That run was rejected as
acceptance evidence; commit `6823150b` returns the cache tree to the runner,
and the accepted cold run completed the post-cache step without a failed-save
annotation.

## Result and boundary

Acceptance: **passed** for the Stage 4a apt-archive cache.

This deliberately does not claim the stronger deferred K2 target of skipping
apt/dpkg installation entirely. A warm runner still unpacks packages and
rebuilds TeX formats; moving to a pinned portable TeX tree or prebuilt image
remains a separate optimization if the remaining 127 seconds becomes the next
quota bottleneck.
