# JE-100C / KR / ko — V0.3-Q

Operator-approved git-only Web source, using the user-supplied Korean PDF. Original PDF is retained unchanged as provenance. Only physical pages 2–12 enter Web output; cover and final page are excluded. No Feishu dependency or publication is implied.

Content is authored in `docs/templates/page_je100c_kr-ko`; shared JE-100C Web components own layout. Native text covers notices, specifications and LCD meanings. Ten source-specific illustration crops include Korean panels and a frame-free LCD operation drawing; reusable unit and icon artwork comes from existing JE-100C assets. Crop coordinates are PDF points (top-left origin), rendered at 4x using PyMuPDF `page.get_pixmap(matrix=fitz.Matrix(4,4), clip=fitz.Rect(*bbox_pt), alpha=False)`. See the illustration manifest for physical source page and hashes. OCR evidence is retained under `ocr/`.

From repository root, using the repository virtualenv:

```sh
AUTO_MANUAL_OSS_ARCHIVE_CONFIG=off AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md --config configs/config.kr.yaml --model JE-100C --region KR --lang ko --data-root manual_sources/JE-100C/KR/ko/V0.3-Q/phase2 --staging-root /private/tmp/je100c-kr-build --skip-root-index
python -m sphinx -W -D language=ko -b html /private/tmp/je100c-kr-build/docs/_build/JE-100C/KR/ko/md /private/tmp/je100c-kr-html
python -m http.server 18841 --bind 127.0.0.1 --directory /private/tmp/je100c-kr-html
```

Preview: `http://127.0.0.1:18841/manual_je100c_kr_ko.html`.

Operator-approved Web correction: physical p6 F8 label “남은 배터리 용량” is corrected to “오류 코드”, including image alt text. Original PDF remains unchanged. Source terminology (사용자 매뉴얼 / 표시등) is preserved even where the checker prefers alternatives. `CAPABILITY_ROW_MISSING` remains a warning: no live capability-table row is introduced for this Git-only candidate. Publication approval and production admission are separate from this preview.
