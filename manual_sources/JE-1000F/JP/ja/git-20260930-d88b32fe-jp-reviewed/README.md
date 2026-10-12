# JE-1000F JP reviewed Web source

This immutable snapshot preserves the complete Japanese Web manual reviewed
with the operator against the 2026-06-05 V1.0 PDF. The release authority is the
reviewed v23 DOM, including native HTML tables and text, target artwork,
transparent shared LCD/button icons and final label alignment.

`web/ja/manual_je1000f_jp.md` is the durable MyST publishing input. Its raw HTML
contains native semantic elements, not screenshots of tables or prose.
Scoped style blocks preserve the accepted layout; the repository Web theme
still provides the surrounding manual center. All 69 artwork files are local.

Rebuild with strict Sphinx from `web/ja` into a new directory. Seal the
source manifest and exact Git commit using `tools.web.frozen_source_evidence`,
then use the ordinary publish assembler against current Hello-Docs/main.
Do not dispatch a live-data rebuild as a substitute for this reviewed source.
The phase2 JP check is a regression check; it does not validate this source's
reviewed body. This Git-only release does not modify online tables.

Zoom links follow the assembled image URL, so pooled production assets remain
openable. The hidden Sphinx navigation title is scoped by ID to survive the
production locale wrapper. Both adaptations leave the reviewed body unchanged.
