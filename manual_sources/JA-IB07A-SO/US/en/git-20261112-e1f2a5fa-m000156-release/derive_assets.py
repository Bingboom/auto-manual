"""Reproduce reviewed figure crops and byte-identical shared artwork bindings."""

from pathlib import Path
import hashlib, json, shutil
import fitz

P = Path(__file__).resolve().parent
R = next(p for p in P.parents if (p / "build.py").is_file())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    data = json.loads((P / "source/asset_decisions.json").read_text())
    recipe = json.loads((P / "source/asset_recipes.json").read_text())
    doc = fitz.open(P / "source/original.pdf")
    assert sha(P / "source/original.pdf") == recipe["source_sha256"]
    for key, entry in recipe["assets"].items():
        target = P / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry["mode"] == "shared-reuse":
            source = R / entry["repo_path"]
            assert sha(source) == entry["repo_sha256"]
            shutil.copy2(source, target)
        else:
            page = doc[entry["physical_page"] - 1]
            box = entry.get("clip_points") or [
                v * (page.rect.width if i % 2 == 0 else page.rect.height)
                for i, v in enumerate(entry["clip_fraction"])
            ]
            pix = page.get_pixmap(
                matrix=fitz.Matrix(3, 3), clip=fitz.Rect(box), alpha=False
            )
            pix.save(target)
            entry["resolved_clip_points"] = box
        data["assets"][key] = {
            **entry,
            "sha256": sha(target),
            "bytes": target.stat().st_size,
        }
    (P / "source/asset_decisions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    print(str(P) + ": " + str(len(recipe["assets"])) + " reviewed artwork bindings")


if __name__ == "__main__":
    main()
