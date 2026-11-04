# JHP-5000C / US / EN source alignment

New immutable edition derived from `git-20261010-051169dd-web-layout`. The existing three-language edition remains unchanged.

The current single-language Feishu attachment is `source/review-reference.pdf` (SHA-256 `3381c816e6bb75bc5e790bcba3faacbb3ad199f1a41cc53c5092368bcd945250`; 28 pages). It is the acceptance baseline for all English content and layout. The older root PDF and existing artwork provenance remain the origin of preserved vector illustrations, not the current content authority. Cover and printed TOC remain excluded as historically approved.

This edition restores the missing WARNING before Backup UPS and the missing cascade-connection CAUTION after its figure, both from current physical page 13 / printed page 10. All warning paragraphs and three equipment categories remain native HTML and retain their source order. No artwork is redrawn or replaced by a full-page image.

User instructions: “一个一个修 复核通过 就打钩”; “本地构建复核通过就可以了”. Local acceptance evidence is separate from release status. Publication is pending.

Run `python <package>/refresh_manifest.py`, then `python <package>/rebuild.py --language en --output <unused-path>`.


Residual review supersedes the first local pass. See `evidence/legacy-declaration-audit.json` for every inherited layout declaration and current physical page; `evidence/review.md` for acceptance and exceptions. Front cover and printed TOC are intentionally excluded.

## Authorized release snapshot

This immutable -release copy binds the fully reviewed candidate at cd3703837dfc119790906351486d1517772572eb under MA-381 (operator: 授权本批逐本全绿后合入上线; local acceptance: 本地构建复核通过就可以了). Candidate content, CSS and artwork remain unchanged. Original repo_inputs pins are preserved. Current approval and byte-equivalence evidence supersede inherited candidate-status statements for this copy only. Publication itself remains a separate transaction.
