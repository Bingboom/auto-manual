# Charging figure labels: bounded correction

Discovery: four fresh-PDF manuals bind solar diagrams as caption_mode=none; positioned PDF labels fall through as ordinary prose. Shared ReferenceFigure already supports base-art-live-copy, with desktop positioned labels and mobile labels inside the same gray panel. Existing text-free artwork includes the label space and must remain byte-identical.

Scope: bind exactly SolarSaga 200 × 2 and SolarSaga 100 Air × 4 to their two diagrams in each of uk/pt/nl/pl. Also bind the vehicle label in the car charging diagram, explicitly by language (uk/pt/nl/pl). The operator approved both solar layouts via screenshots, then requested this car-label correction. All five reference diagrams were checked against positioned PDF blocks: UPS and AC have no remaining interior source text. Consume matched source blocks once. Keep charging prose, existing five languages, all other targets, CSS and artwork unchanged. Preserve historical frozen packages; create a new immutable package.

Phases: optional declared PDF label binding; exact-source/asset/geometry failure tests; four shared-IR builds; text/image parity and available visual evidence; engineering PR then four-language publication and RTD verification.

Validation: focused unittest; Ruff; full unittest; maintainability; doc links; US fixture check; four strict Sphinx builds; cold replay; four-page text order and assets identical; labels inside reference panels at desktop and mobile; publish-scope and live revision checks.

Branch: managed isolated worktree, tracked-clean local base 6962b552 tree equals live main 99edfd22 tree e4d7e8ee. start_branch.sh Git fetch timed out after 25 seconds; branch created from this verified equivalent base. No foreign files were modified.

Acceptance evidence: operator screenshots approved both solar label positions. Final car-inclusive preview serves on port 18856; all four pages have three live labels inside their panels and no standalone label paragraphs. Browser automation timed out, so automated viewport screenshots are not claimed. Car position feedback is pending.
