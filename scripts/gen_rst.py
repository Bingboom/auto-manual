import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
SECTIONS = DOCS / "_sections"

def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def esc_latex(s: str) -> str:
    # minimal safe escape for raw latex args
    return (s or "").replace("\\", "\\textbackslash ").replace("{", "\\{").replace("}", "\\}")

def tex_newlines(s: str) -> str:
    # CSV contains literal \n -> make it real newlines
    s = (s or "").replace("\\n", "\n")
    # then emit as LaTeX line breaks
    return esc_latex(s).replace("\n", "\\\\ ")

def block_to_rst(row) -> str:
    t = (row.get("type") or "").strip()
    text = (row.get("text") or "").strip()
    p1 = (row.get("param1") or "").strip()
    p2 = (row.get("param2") or "").strip()
    p3 = (row.get("param3") or "").strip()

    if t == "p":
        return text + "\n\n"

    if t == "ups_layout":
        left = text
        right = p1
        desc = p2
        return f"""
.. raw:: latex

   \\hbUPSLayout{{{esc_latex(left)}}}{{{esc_latex(right)}}}{{{tex_newlines(desc)}}}

"""

    if t == "admonition_list":
        label = p1 or "CAUTION"
        items = [x.strip() for x in text.split(";") if x.strip()]
        # we pass ready-made \item ... tokens to LaTeX
        item_lines = "".join([f"\\item {esc_latex(i)} " for i in items])
        return f"""
.. raw:: latex

   \\hbAdmonitionList{{{esc_latex(label)}}}{{{item_lines}}}

"""

    if t == "highlight_bar":
        return f"""
.. raw:: latex

   \\hbHighlightBar{{{esc_latex(text)}}}

"""

    if t == "warranty_block":
        title = text
        body = p1
        return f"""
.. raw:: latex

   \\hbWarrantyBlock{{{esc_latex(title)}}}{{{tex_newlines(body)}}}

"""

    if t == "warranty_years":
        left_year = text
        left_title = p1
        right_year = p2
        right_title = p3
        return f"""
.. raw:: latex

   \\hbWarrantyYears{{{esc_latex(left_year)}}}{{{esc_latex(left_title)}}}{{{esc_latex(right_year)}}}{{{esc_latex(right_title)}}}

"""

    return text + "\n\n"

def main():
    SECTIONS.mkdir(parents=True, exist_ok=True)

    outline = read_csv(DATA / "outline.csv")
    blocks = read_csv(DATA / "blocks.csv")

    outline = [o for o in outline if o.get("include", "1").strip() == "1"]
    outline.sort(key=lambda x: int(x["order"]))

    blocks_by_sec = {}
    for b in blocks:
        blocks_by_sec.setdefault(b["section_id"], []).append(b)
    for sec_id, arr in blocks_by_sec.items():
        arr.sort(key=lambda x: int(x["order"]))

    section_files = []
    for sec in outline:
        sec_id = sec["section_id"]
        title = sec["title"].strip()
        fname = f"{sec_id}.rst"
        section_files.append(fname)

        buf = f"{title}\n" + ("=" * len(title)) + "\n\n"
        for b in blocks_by_sec.get(sec_id, []):
            buf += block_to_rst(b)

        (SECTIONS / fname).write_text(buf, encoding="utf-8")

    doc_title = "HB Manual Demo"
    index = f"{doc_title}\n" + ("=" * len(doc_title)) + "\n\n.. toctree::\n   :maxdepth: 2\n\n"
    for f in section_files:
        index += f"   _sections/{f[:-4]}\n"
    (DOCS / "index.rst").write_text(index, encoding="utf-8")

    print("OK: generated", len(section_files), "pages")

if __name__ == "__main__":
    main()