#!/usr/bin/env python3
"""Render the four new JE-1000F EU Web books from the frozen AI extraction.

The direct source JSON and cropped figures are immutable release inputs. This
script only formats that source; it does not translate or fill missing copy.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import struct


HERE = Path(__file__).resolve().parent
WEB_CSS = HERE / "source/web_manual.css"
SECTION_INDEX = json.loads((HERE / "source/section_index.json").read_text(encoding="utf-8"))
FRONT_BACK = json.loads((HERE / "source/front_back_source.json").read_text(encoding="utf-8"))
WARRANTY = json.loads((HERE / "source/warranty_columns.json").read_text(encoding="utf-8"))
APP = json.loads((HERE / "source/app_sections.json").read_text(encoding="utf-8"))
SYMBOLS = json.loads((HERE / "source/symbols.json").read_text(encoding="utf-8"))
LCD = json.loads((HERE / "source/lcd_indicators.json").read_text(encoding="utf-8"))
OPERATION_TABLES = json.loads((HERE / "source/operation_tables.json").read_text(encoding="utf-8"))
LANGUAGES = ("uk", "pt", "nl", "pl")
SOURCE_SHA256 = "c38415f5c2d96832119105d963737a10901e470f70c5e7518ef6404f83625eb2"
PREFACE_BREAKS = {
    "uk": ("Відповідно до законів", "Зверніть увагу", "* Зображення"),
    "pt": ("Em conformidade", "Observe que", "* As imagens"),
    "nl": ("Volgens de wet", "Houd er rekening", "* De afbeeldingen"),
    "pl": ("Zgodnie z przepisami", "Należy pamiętać", "* Obrazy"),
}
UK_SOURCE_CORRECTION = (
    "Aby uzyskać maksymalną moc wyjściową, należy użyć kabla USB-C do USB-C 5 A (20 V DC / 5 A, 100 W).",
    "Щоб отримати максимальну вихідну потужність, використовуйте кабель USB-C до USB-C 5 A (20 В DC/5 A, 100 Вт).",
)


def squash(raw: str) -> str:
    raw = re.sub(r"jack-\s*\n\s*ery\.com", "jackery.com", raw, flags=re.I)
    return " ".join(raw.split())


def key(raw: str) -> str:
    return squash(raw).casefold()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as image_file:
        header = image_file.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"invalid PNG source: {path}")
    return struct.unpack(">II", header[16:24])


def figure_html(figure: dict, *, alt: str) -> str:
    name = Path(figure["path"]).name
    width, height = png_dimensions(HERE / "figures" / figure["locale"] / name)
    return (f'<figure><img src="assets/{name}" alt="{html.escape(alt)}" '
            f'width="{width}" height="{height}" loading="lazy" '
            'style="max-width:100%;height:auto"></figure>')


def is_heading(raw: str) -> bool:
    value = squash(raw)
    letters = "".join(char for char in value if char.isalpha())
    return bool(letters) and letters == letters.upper() and len(value) <= 110


def prose(raw: str, *, lang: str | None = None) -> list[str]:
    value = squash(raw)
    if lang == "uk" and UK_SOURCE_CORRECTION[0] in value:
        value = value.replace(*UK_SOURCE_CORRECTION)
    if not value or re.fullmatch(r"\d{1,3}", value):
        return []
    if "•" in value:
        lead, *items = value.split("•")
        result = [f"<p>{html.escape(lead.strip())}</p>"] if lead.strip() else []
        result.extend(["<ul>", *[f"<li>{html.escape(item.strip())}</li>" for item in items if item.strip()], "</ul>"])
        return result
    if is_heading(value):
        return [f"<h3>{html.escape(value)}</h3>"]
    return [f"<p>{html.escape(value)}</p>"]


def find_section_starts(source: dict, titles: list[str]) -> list[tuple[int, float, str]]:
    starts = []
    ids = SECTION_INDEX["section_ids"]
    for section_id, title in zip(ids, titles):
        expected_page = next(section["physical_pages"][0] for section in source["sections"] if section["id"] == section_id)
        matches = [
            (page["physical_page"], block["bbox"][1])
            for page in source["pages"]
            for block in page["blocks_visual_order"]
            if page["physical_page"] == expected_page and key(block["text"]) == key(title)
        ]
        if not matches:
            raise ValueError(f"section {section_id} title has {len(matches)} matches")
        starts.append((*min(matches), section_id))
    if starts != sorted(starts):
        raise ValueError("section headings are not in page order")
    return starts


def native_table(rows: list[tuple[str, str]], headings: tuple[str, str]) -> list[str]:
    result = [
        '<div class="manual-table-scroll" style="overflow-x:auto;max-width:100%">',
        '<table class="manual-table"><thead><tr>',
        f'<th scope="col">{html.escape(headings[0])}</th>',
        f'<th scope="col">{html.escape(headings[1])}</th>',
        "</tr></thead><tbody>",
    ]
    for label, value in rows:
        result.append(f'<tr><th scope="row">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>')
    result.extend(["</tbody></table>", "</div>"])
    return result


def symbol_headings(source: dict) -> tuple[str, str]:
    page_no = next(section["physical_pages"][0] for section in source["sections"] if section["id"] == "symbols")
    page = next(page for page in source["pages"] if page["physical_page"] == page_no)
    lines = next(block["text"].splitlines() for block in page["blocks_visual_order"] if 365 <= block["bbox"][1] < 390 and len(block["text"].splitlines()) == 2)
    return squash(lines[0]), squash(lines[1])


def pictogram_table(lang: str, headings: tuple[str, str]) -> list[str]:
    result = [
        '<div class="manual-table-scroll" style="overflow-x:auto;max-width:100%">',
        '<table class="manual-table"><thead><tr>',
        f'<th scope="col">{html.escape(headings[0])}</th><th scope="col">{html.escape(headings[1])}</th>',
        '</tr></thead><tbody>',
    ]
    for row in SYMBOLS["locales"][lang]["pictograms"]:
        name = Path(row["icon_path"]).name
        width, height = png_dimensions(HERE / "figures" / lang / name)
        result.append(f'<tr><th scope="row"><img src="assets/{name}" alt="" width="{width}" height="{height}" style="max-width:48px;height:auto"></th><td>{html.escape(row["meaning"])}</td></tr>')
    result.extend(["</tbody></table></div>"])
    return result


def lcd_content(lang: str, figures: list[dict]) -> list[str]:
    figure = next(item for item in figures if item["slug"] == "lcd_display")
    result = [
        figure_html(figure, alt=SECTION_INDEX["languages"][lang]["titles"][4]),
        '<div class="manual-table-scroll" style="overflow-x:auto;max-width:100%"><table class="manual-table"><tbody>',
    ]
    for row in LCD["locales"][lang]["rows"]:
        result.append(f'<tr><th scope="row">{row["number"]}</th><td><strong>{html.escape(row["label"])}</strong><br>{html.escape(row["meaning"])}</td></tr>')
    result.extend(["</tbody></table></div>"])
    return result


def operation_table_content(lang: str, part: str) -> list[str]:
    record = OPERATION_TABLES["locales"][lang][part]
    if part == "lcd_mode":
        result = ['<div class="manual-table-scroll" style="overflow-x:auto;max-width:100%"><table class="manual-table"><tbody>']
        for row in record["rows"]:
            mode = record["modes"][row["mode_index"]]["text"]
            if lang == "pt":
                mode = mode.replace("continuame nte", "continuamente")
            result.append(f'<tr><th scope="row">{html.escape(mode)}</th><td><strong>{html.escape(row["action"]["text"])}</strong><br>{html.escape(row["instruction"]["text"])}</td></tr>')
        result.extend(["</tbody></table></div>"])
        return result
    if part == "restore":
        result = [f'<h3>{html.escape(record["heading"]["text"])}</h3>', f'<p>{html.escape(record["intro"]["text"])}</p>']
        for column in record["columns"]:
            result.append(f'<h4>{html.escape(column["heading"]["text"])}</h4>')
            result.extend(["<ul>", *[f'<li>{html.escape(item["text"])}</li>' for item in column["items"]], "</ul>"])
        return result
    if part == "shortcuts":
        result = [f'<h3>{html.escape(record["heading"]["text"])}</h3>', '<div class="manual-table-scroll" style="overflow-x:auto;max-width:100%"><table class="manual-table"><thead><tr>']
        result.extend(f'<th scope="col">{html.escape(header["text"])}</th>' for header in record["headers"])
        result.append('</tr></thead><tbody>')
        for row in record["rows"]:
            buttons = " + ".join(html.escape(button["text"]) for button in row["buttons"])
            operation = row["operation"]["text"]
            operation = re.sub(r"^(\d+\s*\S+)\s+(.*)\s+\1$", r"\2 (\1)", operation)
            result.append(f'<tr><th scope="row">{buttons}</th><td>{html.escape(operation)}</td><td>{html.escape(row["function"]["text"])}</td></tr>')
        result.extend(["</tbody></table></div>"])
        return result
    raise ValueError(part)


def table_content(source: dict, section_id: str) -> list[str]:
    if section_id == "troubleshooting":
        rows = [(row["code"], row["action"]) for row in source["tables"][section_id]["rows"]]
        page = next(page for page in source["pages"] if page["physical_page"] == source["tables"][section_id]["physical_page"])
        header = next(block["text"].splitlines() for block in page["blocks_visual_order"] if 250 <= block["bbox"][1] < 260)
        return native_table(rows, (squash(header[0]), squash(header[1])))
    if section_id == "specifications":
        groups = source["tables"][section_id]["groups"]
        page = next(page for page in source["pages"] if page["physical_page"] == source["tables"][section_id]["physical_page"])
        heading_ranges = ((50, 70), (175, 195), (235, 260), (370, 392))
        group_headings = [
            squash(next(block["text"] for block in page["blocks_visual_order"] if low <= block["bbox"][1] < high and is_heading(block["text"])))
            for low, high in heading_ranges
        ]
        result = ['<div class="manual-table-scroll" style="overflow-x:auto;max-width:100%"><table class="manual-table"><tbody>']
        for group_heading, rows in zip(group_headings, groups.values()):
            result.append(f'<tr><th colspan="2" scope="colgroup">{html.escape(group_heading)}</th></tr>')
            for row in rows:
                result.append(f'<tr><th scope="row">{html.escape(row["label"])}</th><td>{html.escape(row["value"])}</td></tr>')
        result.extend(["</tbody></table></div>"])
        return result
    return []


def specification_footnotes(source: dict) -> list[str]:
    page = next(page for page in source["pages"] if page["physical_page"] == source["tables"]["specifications"]["physical_page"])
    blocks = sorted((block for block in page["blocks_visual_order"] if 420 <= block["bbox"][1] < 490), key=lambda item: (item["bbox"][1], item["bbox"][0]))
    notes: list[str] = []
    for block in blocks:
        value = squash(block["text"])
        if value.startswith(("※", "①")):
            notes.append(value)
        elif notes:
            notes[-1] += " " + value
    notes[0] = re.sub(r"\s*®\s*®\s*$", "", notes[0])
    notes[0] = notes[0].replace("USB Type-C", "USB Type-C®", 1).replace("USB-C", "USB-C®", 1)
    return [f"<p>{html.escape(note)}</p>" for note in notes]


def warranty_content(lang: str) -> list[str]:
    record = WARRANTY["locales"][lang]
    blocks = record["blocks"]
    result: list[str] = []
    for part in ("scope", "local_law_note"):
        result.extend(prose(blocks[part]["text"]))
    for heading, content in (
        ("limited_heading", "limited_body"),
        ("period_heading", None),
        ("standard_heading", "standard_body"),
        ("extension_heading", "extension_body"),
        ("exchange_heading", "exchange_body"),
        ("buyer_heading", "buyer_body"),
        ("exclusions_heading", "exclusions_body"),
        ("interpretation_heading", "interpretation_body"),
    ):
        if heading in ("standard_heading", "extension_heading"):
            label, unit, years = [squash(part) for part in blocks[heading]["raw_text"].splitlines() if squash(part)]
            heading_text = f"{years} {unit} — {label}"
        else:
            heading_text = blocks[heading]["text"]
        result.append(f'<h3>{html.escape(heading_text)}</h3>')
        if content == "exclusions_body":
            lead, *items = blocks[content]["text"].split("•")
            result.extend(prose(lead))
            result.extend(["<ul>", *[f"<li>{html.escape(item.strip())}</li>" for item in items if item.strip()], "</ul>"])
        elif content is not None:
            result.extend(prose(blocks[content]["text"]))
    return result


def app_content(lang: str, figures: list[dict]) -> list[str]:
    blocks = APP["locales"][lang]["blocks"]
    result: list[str] = []

    def add_block(name: str, *, heading: bool = False) -> None:
        value = blocks[name]["raw_text"]
        if name == "step_2_1":
            value = re.sub(r"\s{5,}", " + ", value)
        value = squash(value).replace('\\"', '"')
        if heading:
            result.append(f"<h3>{html.escape(value)}</h3>")
        else:
            result.extend(prose(value, lang=lang))

    def add_figure(slug: str) -> None:
        figure = next(item for item in figures if item["slug"] == slug)
        alt = f'{SECTION_INDEX["languages"][lang]["titles"][-1]}: {slug.replace("_", " ")}'
        result.append(figure_html(figure, alt=alt))

    add_block("download_heading", heading=True)
    add_block("download_store")
    add_block("download_qr")
    add_figure("app_qr_and_badges")
    add_block("add_heading", heading=True)
    add_block("step_2_1")
    add_block("step_2_2")
    add_figure("app_add_device")
    add_figure("app_control")
    add_block("step_2_3")
    add_block("bound_note_label", heading=True)
    add_block("bound_note_body")
    add_block("step_2_4")
    add_block("wifi_note_label", heading=True)
    add_block("wifi_note_body")
    add_block("step_2_5")
    add_figure("app_pairing")
    add_block("screenshots_note")
    add_block("bluetooth_caution_label", heading=True)
    add_block("bluetooth_caution_body")
    unbind_heading, unbind_body = blocks["unbind"]["raw_text"].split("\n", 1)
    result.append(f"<h3>{html.escape(squash(unbind_heading))}</h3>")
    result.extend(prose(unbind_body, lang=lang))
    add_block("notes_heading", heading=True)
    for name in ("enable", "disable", "reset"):
        add_block(name)
    return result


def chapter_nav(titles: list[str]) -> str:
    links = [
        f'<li><a href="#{section_id}">{html.escape(title)}</a></li>'
        for section_id, title in zip(SECTION_INDEX["section_ids"], titles)
    ]
    return '<nav aria-label="Chapters"><ul>' + "".join(links) + "</ul></nav>"


def write_book(lang: str, output_root: Path) -> dict:
    source_file = HERE / "source" / f"{lang}_direct_source.json"
    source = json.loads(source_file.read_text(encoding="utf-8"))
    figures_file = HERE / "source" / f"{lang}_figure_manifest.json"
    figures = json.loads(figures_file.read_text(encoding="utf-8"))["figures"]
    if source["source_sha256"] != SOURCE_SHA256 or FRONT_BACK["source_sha256"] != SOURCE_SHA256:
        raise ValueError("designated AI SHA-256 mismatch")
    spec = SECTION_INDEX["languages"][lang]
    titles = spec["titles"]
    starts = find_section_starts(source, titles)
    dest = output_root / "JE-1000F" / "EU" / lang / "md"
    dest.mkdir(parents=True, exist_ok=True)
    assets = dest / "assets"
    assets.mkdir(exist_ok=True)
    static = dest / "_static"
    static.mkdir(exist_ok=True)
    shutil.copy2(WEB_CSS, static / WEB_CSS.name)
    for figure in figures:
        original = HERE / "figures" / lang / Path(figure["path"]).name
        if hashlib.sha256(original.read_bytes()).hexdigest() != figure["sha256"]:
            raise ValueError(f"figure hash mismatch: {original}")
        shutil.copy2(original, assets / original.name)
    for row in SYMBOLS["locales"][lang]["pictograms"]:
        original = HERE / "figures" / lang / Path(row["icon_path"]).name
        if hashlib.sha256(original.read_bytes()).hexdigest() != row["icon_sha256"]:
            raise ValueError(f"pictogram hash mismatch: {original}")
        shutil.copy2(original, assets / original.name)

    preface = FRONT_BACK["locales"][lang]["preface"]["text"]
    preface = re.sub(r"^(?:UA|PT|NL|PL)\s*\n", "", preface)
    preface = re.sub(r"\nВАЖЛИВО\s*$", "", preface)
    for marker in PREFACE_BREAKS[lang]:
        preface = preface.replace("\n" + marker, "\n\n" + marker)
    chunks = preface.split("\n\n")
    body = [
        f'# Jackery Explorer 1000 — {spec["label"]}',
        "",
        "Model: JE-1000F · hello.eu@jackery.com",
        "",
        "## Introduction",
        "",
        *[f"<p>{html.escape(squash(chunk))}</p>" for chunk in chunks if squash(chunk)],
        "",
        "## Contents",
        "",
        chapter_nav(titles),
        "",
    ]
    section_number = -1
    emitted_figures = 0
    pictograms_emitted = False
    operation_tables_emitted: set[str] = set()
    for page in source["pages"]:
        number = page["physical_page"]
        blocks = sorted(page["blocks_visual_order"], key=lambda item: (item["bbox"][1], item["bbox"][0]))
        page_figures = sorted((figure for figure in figures if figure["physical_page"] == number), key=lambda item: item["clip_points"][1])
        if number in LCD["locales"][lang]["pages"]:
            page_figures = []
        if number in (APP["locales"][lang]["blocks"]["title"]["physical_page"], APP["locales"][lang]["blocks"]["reset"]["physical_page"]):
            page_figures = []
        figure_pos = 0
        for block in blocks:
            y = block["bbox"][1]
            while (figure_pos < len(page_figures)
                   and page_figures[figure_pos]["clip_points"][1] <= y
                   and section_number >= 0
                   and page_figures[figure_pos]["section_id"] == starts[section_number][2]):
                figure = page_figures[figure_pos]
                alt = f'{titles[max(section_number, 0)]}: {figure["slug"].replace("_", " ")}'
                body.extend([figure_html(figure, alt=alt), ""])
                emitted_figures += 1
                figure_pos += 1
            if (section_number + 1 < len(starts)
                    and number == starts[section_number + 1][0]
                    and abs(y - starts[section_number + 1][1]) < 0.01
                    and key(block["text"]) == key(titles[section_number + 1])):
                section_number += 1
                section_id = starts[section_number][2]
                body.extend([f'<span id="{section_id}"></span>', f'## {titles[section_number]}', ""])
                if section_id == "warranty":
                    body.extend(warranty_content(lang))
                    body.append("")
                if section_id == "symbols":
                    rows = [(row["label"], row["meaning"]) for row in SYMBOLS["locales"][lang]["rows"]]
                    body.extend(native_table(rows, symbol_headings(source)))
                    body.append("")
                if section_id == "lcd_display":
                    body.extend(lcd_content(lang, figures))
                    body.append("")
                    emitted_figures += 1
                if section_id == "app_setup":
                    body.extend(app_content(lang, figures))
                    body.append("")
                    emitted_figures += 4
                continue
            if section_number < 0:
                raise ValueError(f"text before first section on page {number}")
            section_id = starts[section_number][2]
            if section_id == "operations":
                for part in ("lcd_mode", "restore", "shortcuts"):
                    record = OPERATION_TABLES["locales"][lang][part]
                    if (part not in operation_tables_emitted and number == record["physical_page"]
                            and y >= record["source_region"][1]):
                        body.extend(operation_table_content(lang, part))
                        body.append("")
                        operation_tables_emitted.add(part)
                    if number == record["physical_page"] and record["source_region"][1] <= y < record["source_region"][3]:
                        break
                else:
                    part = None
                if part is not None and number == record["physical_page"] and record["source_region"][1] <= y < record["source_region"][3]:
                    continue
            if (section_id == "symbols" and not pictograms_emitted
                    and number == SYMBOLS["locales"][lang]["pictogram_page"]):
                body.extend(pictogram_table(lang, symbol_headings(source)))
                body.append("")
                pictograms_emitted = True
            if section_id == "warranty" and number == WARRANTY["locales"][lang]["physical_page"]:
                continue
            if section_id == "app_setup":
                continue
            if section_id == "lcd_display":
                continue
            if section_id == "troubleshooting" and number == source["tables"]["troubleshooting"]["physical_page"] and y >= 250:
                continue
            if section_id == "symbols" and number == SYMBOLS["locales"][lang]["physical_page"] and y >= 370:
                continue
            if section_id == "symbols" and number == SYMBOLS["locales"][lang]["pictogram_page"] and y < 180:
                continue
            if section_id == "specifications" and number == source["tables"]["specifications"]["physical_page"]:
                continue
            body.extend(prose(block["text"], lang=lang))
            body.append("")
        while figure_pos < len(page_figures):
            figure = page_figures[figure_pos]
            if figure["section_id"] != starts[section_number][2]:
                raise ValueError(f"figure placed in wrong section: {figure['slug']} on {number}")
            alt = f'{titles[max(section_number, 0)]}: {figure["slug"].replace("_", " ")}'
            body.extend([figure_html(figure, alt=alt), ""])
            emitted_figures += 1
            figure_pos += 1
        if section_number >= 0:
            section_id = starts[section_number][2]
            if section_id in ("troubleshooting", "specifications") and number == source["tables"][section_id]["physical_page"]:
                body.extend(table_content(source, section_id))
                if section_id == "specifications":
                    body.extend(specification_footnotes(source))
                body.append("")
    if section_number + 1 != len(starts) or emitted_figures != len(figures) or len(operation_tables_emitted) != 3:
        raise ValueError(f"incomplete book {lang}: sections={section_number+1}, figures={emitted_figures}")
    declaration = FRONT_BACK["shared"]["eu_declaration"]
    body.extend(["## EU declaration and manufacturer", "", *prose(declaration["blocks_visual_order"][0]["text"]), ""])
    for block in sorted(declaration["blocks_visual_order"][1:], key=lambda item: (item["bbox"][1], item["bbox"][0])):
        body.extend(prose(block["text"]))
        body.append("")
    manual_name = f"manual_je1000f_eu_{lang}"
    (dest / f"{manual_name}.md").write_text("\n".join(body), encoding="utf-8")
    (dest / "index.md").write_text(f'# Jackery Explorer 1000 — {spec["label"]}\n\n```{{toctree}}\n:maxdepth: 2\n\n{manual_name}\n```\n', encoding="utf-8")
    (dest / "conf.py").write_text(
        f'project = "Jackery Explorer 1000"\nextensions = ["myst_parser"]\nsource_suffix = {{".md": "markdown"}}\nroot_doc = "index"\nhtml_theme = "furo"\nlanguage = "{lang}"\nhtml_static_path = ["_static"]\nhtml_css_files = ["web_manual.css"]\n'
        'from pathlib import Path\nimport shutil\n'
        'def _copy_assets(app, exception):\n'
        '    if exception is None:\n'
        '        shutil.copytree(Path(__file__).parent / "assets", Path(app.outdir) / "assets", dirs_exist_ok=True)\n'
        'def setup(app):\n'
        '    app.connect("build-finished", _copy_assets)\n',
        encoding="utf-8",
    )
    return {"locale": lang, "physical_pages": spec["physical_pages"], "sections": len(starts), "figures": emitted_figures, "source_sha256": SOURCE_SHA256}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--langs", nargs="+", choices=LANGUAGES, default=list(LANGUAGES))
    args = parser.parse_args()
    result = [write_book(lang, args.output_root) for lang in args.langs]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
