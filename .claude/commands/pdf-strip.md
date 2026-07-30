---
description: 删除 PDF 的首页/尾页/指定页,输出 _stripped 副本(不动原件)并核对页数
---

Strip pages from a PDF and hand back a `_stripped` copy. The operator's
recurring form: 「把这个 pdf 删除第一页」「把最后两页去掉」.

Input: $ARGUMENTS — a PDF path, optionally followed by a page spec. Page spec
forms (1-based, same wording the operator uses):

- (empty) → delete page 1 (the default: cover / internal circulation page)
- `first N` / `前N页` → delete pages 1..N
- `last N` / `后N页` / `最后N页` → delete the last N pages
- explicit pages/ranges, e.g. `2` or `3-5`

Rules:

1. **Never overwrite the original.** Output is a sibling file with
   `_stripped` inserted before `.pdf`.
2. Use the repo venv's PyMuPDF. Run this shape (adjust `pages_to_delete`):

   ```bash
   .venv/bin/python - "<input.pdf>" <<'PY'
   import sys
   import fitz

   src = sys.argv[1]
   doc = fitz.open(src)
   before = doc.page_count
   pages_to_delete = [0]  # 0-based; e.g. last 2 -> [before-2, before-1]
   for index in sorted(pages_to_delete, reverse=True):
       doc.delete_page(index)
   out = src[: -len(".pdf")] + "_stripped.pdf" if src.lower().endswith(".pdf") else src + "_stripped.pdf"
   doc.save(out)
   print(f"{before} -> {doc.page_count} pages: {out}")
   PY
   ```

3. Report the before → after page count so the operator can sanity-check
   (e.g. 62 → 61), then send the `_stripped` file back to the operator.
4. If the requested pages don't exist (e.g. `last 3` on a 2-page PDF), stop
   and say so — never guess.
