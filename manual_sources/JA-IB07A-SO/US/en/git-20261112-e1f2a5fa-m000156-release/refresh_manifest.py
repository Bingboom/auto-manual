"""Refresh source/input manifests only after the source changes have been reviewed."""

from pathlib import Path
import hashlib, json
import render

P = Path(__file__).resolve().parent
R = next(p for p in P.parents if (p / "build.py").is_file())


def row(p):
    return {
        "path": p.relative_to(P).as_posix(),
        "size": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }


def main():
    path = P / "source_manifest.json"
    m = json.loads(path.read_text())
    m["inputs"] = [
        row(p)
        for p in sorted(P.rglob("*"))
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.relative_to(P).parts[0] in ["source", "assets"]
    ]
    m["inputs"] += [
        row(P / n) for n in ["render.py", "derive_assets.py", "refresh_manifest.py"]
    ]
    m["shared_component_exceptions"] = render.exceptions(
        json.loads((P / "source/transcription.json").read_text())
    )
    m["repo_inputs"] = [
        {
            "path": "docs/renderers/contracts/web_presentation/target_overlays.json",
            "sha256": hashlib.sha256(
                (
                    R / "docs/renderers/contracts/web_presentation/target_overlays.json"
                ).read_bytes()
            ).hexdigest(),
        }
    ]
    reused = json.loads((P / "source/asset_recipes.json").read_text())[
        "assets"
    ].values()
    for entry in reused:
        if entry["mode"] == "shared-reuse" and not any(
            x["path"] == entry["repo_path"] for x in m["repo_inputs"]
        ):
            m["repo_inputs"].append(
                {"path": entry["repo_path"], "sha256": entry["repo_sha256"]}
            )
    path.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n")
    frozen = {
        **m,
        "inputs": [
            row(p)
            for p in sorted(P.rglob("*"))
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.name != "frozen_source_manifest.json"
        ],
    }
    (P / "frozen_source_manifest.json").write_text(
        json.dumps(frozen, ensure_ascii=False, indent=2) + "\n"
    )
    print(len(m["inputs"]), "source inputs; ", len(frozen["inputs"]), "package files")


if __name__ == "__main__":
    main()
