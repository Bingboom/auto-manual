"""Cold replay byte parity and hash-rejection checks using disposable copies.

Original source, artwork and repository styles are never mutated by this gate.
Freeze web/en, web/fr, web/es and refresh source_manifest.json before running.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
REPO = next(p for p in SOURCE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.web.language_release_evidence import _file_inventory  # noqa: E402


def validate(evidence):
    evidence.mkdir(parents=True, exist_ok=False)
    results = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for language in ["en", "fr", "es"]:
        target = evidence / language
        subprocess.run([sys.executable, str(SOURCE / "rebuild.py"), "--language", language,
                        "--output", str(target)], check=True, env=env, cwd=REPO)
        expected, actual = _file_inventory(SOURCE / "web" / language), _file_inventory(target)
        if expected != actual:
            raise ValueError("cold replay differs from frozen " + language)
        results.append({"language": language, "file_count": len(actual), "byte_parity": True})

    # Bind the real rebuild's inventory gate to disposable copies. Mutations
    # must fail before assembly; imported shared APIs remain the trusted ones.
    source_copy, repo_copy = evidence / "source-copy", evidence / "repo-copy"
    shutil.copytree(SOURCE, source_copy)
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    for row in manifest["repo_inputs"]:
        dest = repo_copy / row["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / row["path"], dest)
    module_spec = importlib.util.spec_from_file_location("jhp3000d_native_rebuild", SOURCE / "rebuild.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    module.SOURCE_ROOT, module.REPO_ROOT = source_copy, repo_copy
    tampering = []
    for label, base, relative in [
        ("copy", source_copy, "source/en/content.json"),
        ("art", source_copy, "assets/power.svg"),
        ("source-style", source_copy, "source/presentation.css"),
        ("shared-style", repo_copy, "docs/renderers/contracts/web_manual.css"),
        ("theme", repo_copy, "docs/renderers/contracts/manual_theme.yaml"),
    ]:
        path = base / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        try:
            module.rebuild(evidence / ("rejected-" + label), "en")
        except ValueError as error:
            if str(error) != "input changed: " + relative:
                raise ValueError("tamper was not rejected by the expected input binding") from error
            tampering.append({"kind": label, "path": relative, "rejected": True})
        else:
            raise ValueError("tampered " + label + " was accepted")
        finally:
            path.write_bytes(original)
    report = {"cold_replay": results, "tamper_rejection": tampering}
    (evidence / "replay_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    validate(args.evidence_dir.resolve())
