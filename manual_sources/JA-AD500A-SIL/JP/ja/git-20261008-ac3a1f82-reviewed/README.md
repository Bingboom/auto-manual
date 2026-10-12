# JA-AD500A-SIL JP Japanese approved release

Operator instruction “上线提交发布”, 2026-10-08; MA-272, engineering PR #1460.
The [original candidate](../git-20261008-ac3a1f82/README.md) remains immutable.
`approval.json` binds the original PDF, candidate commit, MyST, CSS and HTML.
The adapter rechecks frozen inputs and freshly assembles the existing shared
components before replay. Source wording, all artwork and documented numerical
and warranty concerns remain unchanged. The filename version is recorded;
the printed-manual version remains unknown. This is a Git-only source with
no phase2 registration or live-table dependency.

From the repository root, rebuild in new directories:

```sh
python3 manual_sources/JA-AD500A-SIL/JP/ja/git-20261008-ac3a1f82-reviewed/render.py /tmp/dc-input-jp-reviewed-new
python3 -m sphinx -W --keep-going -b html /tmp/dc-input-jp-reviewed-new /tmp/dc-input-jp-reviewed-html-new
```

Publication follows the existing frozen-language evidence and Hello-Docs
`docs/publish/**` assembly contract. Source commit, release evidence, mirror,
RTD deployment and online resource/browser verification are separate stages.
