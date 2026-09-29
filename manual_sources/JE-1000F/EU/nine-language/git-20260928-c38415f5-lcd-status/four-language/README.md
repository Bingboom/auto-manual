# JE-1000F EU native Web source (uk / pt / nl / pl)

Version: git-20260928-c38415f5-lcd-status. This restores LCD status lines, bold status/emergency-charging labels, numbered troubleshooting steps and consistent below-image App captions while preserving native heading levels, preface paragraphs, safety warnings,
LCD icons, App step numbers, warranty cards and charging labels with shared
components. Dense overview diagrams reuse the corresponding-language source
finished panels, retaining semantic copy in IR and approved Dutch AC errata.
Historical published source packages are unchanged. Every paragraph and table
is native PDF text through manual-ir/v2, ComponentSpec and the public renderer.
Artwork is independently hash-bound; technical product markings and App UI
remain artwork. Printed Contents is omitted. Existing five languages are unchanged.

`source/*.json` preserves fresh native extraction, PDF coordinates, source
hashes, missing-glyph recovery and exact print-wrap normalization.
`source/approved_errata.json` records the approved Ukrainian USB-C sentence
and Dutch AC-button wording fixes. Artwork bindings identify independent
source-compatible graphics and reused repository/live-library images.

The original AI and editable PDF are not copied into the Web package; their
filenames and SHA-256 identities are retained. Re-extraction requires those
originals plus the immutable coordinate recipe at the sibling historical
`git-20260927-c38415f5/four-language` package. Cold public replay of the frozen
IR needs only the committed `web/<language>` tree.
