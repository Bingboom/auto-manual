"""Refresh the frozen source inventory after reviewed source or geometry edits."""

import json, hashlib, fitz
from pathlib import Path

S = Path(__file__).resolve().parents[1]
R = next(p for p in S.parents if (p / "build.py").is_file())
D = fitz.open(next(S.glob("*.pdf")))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
base = """/* Native figure coordinates only; shared theme owns headings, prose and semantic tables. */
.native-figure{max-width:720px;margin:1rem auto;min-width:0;}
.native-figure .hb-reference-figure{max-width:none;margin:0;}
#furo-main-content .native-figure img{width:100%!important;height:auto!important;max-height:none;}
.native-figure .hb-reference-live-label{font-family:Arial,"PingFang TC",sans-serif;line-height:1.2;align-items:flex-start;justify-content:flex-start;text-align:left;padding:0;white-space:nowrap;overflow:visible!important;isolation:isolate;}
.native-figure .hb-reference-live-label>span{width:100%;}
.native-figure .hb-reference-live-label strong{font-weight:700;}
.native-lcd-map{max-width:660px;}
.native-app-add{max-width:410px;}
.native-app-result{max-width:680px;}
.native-app-network{max-width:650px;}
.native-reporting-qr{max-width:96px;margin:1rem 0;}
.native-figure .hb-reference-live-label::before,.native-figure .hb-reference-live-label::after{position:absolute;content:"";z-index:-1;pointer-events:none;}
.native-table-scroll{overflow-x:auto;max-width:100%;}
.native-restricted-table{min-width:650px;}
.native-restricted-table th,.native-restricted-table td{text-align:center;vertical-align:middle;padding:.6rem;}
@media(max-width:760px){
 .native-dense{overflow-x:auto;padding-bottom:.5rem;}
 .native-dense>.hb-reference-figure{min-width:680px;}
 .native-restricted-table{font-size:.85rem;}
}
"""
labels = json.loads((S / "source/figure_labels.json").read_text())
figs = json.loads((S / "source/figures.json").read_text())
decor = []
for f in figs:
    box = fitz.Rect(f["bbox"])
    ds = D[f["page"] - 1].get_drawings()
    pseudo = {}
    for ix in f["removed_drawing_indices"]:
        d = ds[ix]
        r = d["rect"]
        fill = d["fill"]
        if not fill:
            continue
        local = [
            v
            for v in labels
            if v["figure"] == f["id"]
            and r.contains(
                fitz.Point(v["native_origin"][0] + 1, v["native_origin"][1] - 2)
            )
        ]
        if not local:
            if f["id"] == "power" and ix == 6:
                local = [
                    v
                    for v in labels
                    if v["figure"] == f["id"] and v["text"].startswith("預設待機")
                ]
            else:
                raise RuntimeError(("empty caption plate", f["id"], ix))
        anchor = min(
            local, key=lambda v: (v["native_origin"][1], v["native_origin"][0])
        )
        line = anchor["line"]
        key = (f["id"], line)
        ps = "before" if key not in pseudo else "after"
        pseudo[key] = ps
        x, y = anchor["native_origin"]
        y -= anchor["font_pt"] * 0.86
        color = "#" + "".join(f"{round(c * 255):02x}" for c in fill)
        rule = f'.native-{f["id"]} [data-source-line="{line}"]::{ps}' + "{"
        rule += f"left:{(r.x0 - x) / box.width * 100:.4f}cqw;top:{(r.y0 - y) / box.width * 100:.4f}cqw;width:{r.width / box.width * 100:.4f}cqw;height:{r.height / box.width * 100:.4f}cqw;background:{color};"
        rule += (
            "clip-path:polygon(50% 0,100% 100%,0 100%);"
            if ix == 6 and f["id"] == "power"
            else "border-radius:1.5cqw;"
        ) + "}"
        base += rule + "\n"
        decor.append(
            {
                "figure": f["id"],
                "physical_page": f["page"],
                "removed_drawing_index": ix,
                "bbox": list(r),
                "label_anchor": line,
                "pseudo": ps,
                "role": "CSS external caption plate",
            }
        )
base += (S / "source/label_geometry.css").read_text()
(S / "source/presentation.css").write_text(base)
(S / "source/caption_frames.json").write_text(
    json.dumps(decor, ensure_ascii=False, indent=2) + "\n"
)
# Refresh source art provenance after fixed markings and transparent shared variant selection.
p = S / "source/asset_decisions.json"
dec = json.loads(p.read_text())
sym = json.loads((S / "source/symbol_provenance.json").read_text())
for d in dec:
    if d["slot"] == "app-result":
        d["bbox"] = [49, 138, 315, 306]
    if d["slot"].startswith("symbol-"):
        row = next(v for v in sym if v["asset_ref"] == d["final_path"])
        d["candidate"] = row["candidate"]
        d["shared_symbol_key"] = row["shared_symbol_key"]
        d["decision"] = "reuse checked shared variant bytes"
    asset_sha = sha(S / d["final_path"])
    if asset_sha == d.get("prior_candidate_sha256"):
        raise ValueError("rejected incomplete artwork restored: " + d["final_path"])
    d["sha256"] = asset_sha
p.write_text(json.dumps(dec, ensure_ascii=False, indent=2) + "\n")
# Six actual native symbol pairs bind caption/glyph provenance into shared admission.
content = json.loads((S / "source/zh-TW/content.json").read_text())
spec = next(
    n["component_spec"]
    for c in content["chapters"]
    for n in c["nodes"]
    if n.get("component_spec", {}).get("component_id") == "HB-TABLE-SYMBOL-ICON"
)
panels = next(s["content"] for s in spec["slots"] if s["role"] == "panels")
for r, meaning in zip(
    sym, [r["meaning_text"] for panel in panels for r in panel], strict=True
):
    r["asset_sha256"] = sha(S / r["asset_ref"])
    r["caption_text"] = meaning
    r["caption_mode"] = "native-extractable-text"
    r["caption_sha256"] = hashlib.sha256(
        D[r["physical_page"] - 1]
        .get_pixmap(
            matrix=fitz.Matrix(4, 4), clip=fitz.Rect(r["caption_bbox"]), alpha=False
        )
        .tobytes("png")
    ).hexdigest()
    b = r["glyph_bbox"]
    c = r["caption_bbox"]
    r["row_bbox"] = [
        min(b[0], c[0]) - 1,
        min(b[1], c[1]) - 1,
        max(b[2], c[2]) + 1,
        max(b[3], c[3]) + 1,
    ]
manifest = {
    "schema_version": "auto-manual-frozen-web-source/v1",
    "target": {
        "model": "JE-1500C",
        "region": "TW",
        "technical_version": "git-20261010-477dfbd7",
        "languages": ["zh-TW"],
    },
    "original_source": {
        "filename": next(S.glob("*.pdf")).name,
        "sha256": "477dfbd75e15c4f5cf0ef1cfb16142467027b8ab272bec04dfd92371d2d4fdc0",
        "page_count": 20,
        "printed_version": "unknown",
        "metadata_title": "16-0102-000487 HTE1181500A-TW-JAK 竖版说明书 A0",
    },
    "physical_page_map": {"zh-TW": [2, 20], "print_cover": 1},
    "web_roots": {"zh-TW": "web/zh-TW"},
    "live_bitable_dependency": False,
    "phase2_enrolled": False,
    "publication_status": "engineering-candidate",
    "symbol_asset_admission": {
        "schema_version": "auto-manual-symbol-asset-admission/v1",
        "locales": {"zh-TW": sym},
    },
}
deps = {
    R / "tools/markdown_bundle.py",
    R / "tools/build_paths.py",
    R / "tools/lang_registry.py",
    R / "tools/language_aliases.py",
    R / "tools/rtd/deployment_receipt.py",
}
for rel in [
    "tools/manual_ir",
    "tools/component_specs",
    "tools/web",
    "tools/asset_pipeline",
    "tools/utils",
    "docs/renderers/contracts",
]:
    deps.update(
        p
        for p in (R / rel).rglob("*")
        if p.is_file() and p.suffix in {".py", ".css", ".json", ".yaml", ".yml"}
    )
for d in dec:
    if d.get("candidate"):
        deps.add(R / d["candidate"])
deps.add(R / "docs/renderers/web/assets/shared/symbols/manifest.json")
manifest["repo_inputs"] = [
    {"path": p.relative_to(R).as_posix(), "size": p.stat().st_size, "sha256": sha(p)}
    for p in sorted(deps)
]
manifest["inputs"] = [
    {"path": p.relative_to(S).as_posix(), "size": p.stat().st_size, "sha256": sha(p)}
    for p in sorted(S.rglob("*"))
    if p.is_file()
    and p.name != "source_manifest.json"
    and "__pycache__" not in p.parts
    and not p.is_relative_to(S / "web")
    and not p.is_relative_to(S / "evidence")
]
(S / "source_manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
)
print(
    "sealed inputs",
    len(manifest["inputs"]),
    "repo inputs",
    len(deps),
    "caption CSS shapes",
    len(decor),
)
