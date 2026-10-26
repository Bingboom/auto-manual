# JE-1000F KR Git-only Web intake discovery

- Original PDF SHA-256 21e693ccffe33acabc887a96a75a3700b2c533722feaa385ee62669217aad392, 14,648,424 bytes, 21 pages, unmodified. Page 1 is a 4499.6×3154.9pt factory drawing sheet (V0.1 first issue, 130×185mm, 2026-7-21, 16-0102-000362); pages 2–21 are 368.5×524.4pt manual pages.
- Request (via the workbench session): convert the JE-1000F KR manual PDF into a Web manual; candidate draft PR only; no merge, publication or online-table write.
- Existing JE-1000F KR data-driven print/Word line (v0.5) has no Web edition. A per-target `page_manifests` override (JE-100C precedent) would also replace the print/Word manifest for JE-1000F_KR, so the JE-3000C KR prepared-document package route is used instead; no config, phase2 or template change.
- All text is outlined. Transcription from 4× renders; Tesseract 5.3.4 kor+eng retained as evidence. No corpus text layer for 16-0102-000362 exists in the repository (corpus ledger row 58 records a text-layer copy only as metadata).
- Web body: PDF pages 3–19. Excluded: 1 factory sheet, 2 cover, 20 blank, 21 QR back cover.
- Checks: shared-style admission, strict Sphinx with language=ko, cold replay and tamper rejection, symbol admission, desktop/mobile browser checks, repository lint/tests/guardrails/doc links and KR target check.
