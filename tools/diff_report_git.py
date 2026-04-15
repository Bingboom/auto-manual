from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

from tools.diff_report_models import DiffRow


def sanitize_token(value: str) -> str:
    out = []
    for ch in value.strip():
        if ch.isalnum() or ch in {"-", "_", "."}:
            out.append(ch)
        else:
            out.append("_")
    text = "".join(out).strip("._")
    return text or "value"


def run_git(args: list[str], *, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


def git_tree_has_entries(repo_root: Path, *, ref: str, pathspec: str) -> bool:
    output = run_git(["ls-tree", "-r", "--name-only", ref, "--", pathspec], cwd=repo_root)
    return bool(output.strip())


def pathspec_from_root(repo_root: Path, tracked_root: Path) -> str:
    try:
        return tracked_root.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return tracked_root.as_posix()


def detect_initial_baseline(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
    file_rows: list[DiffRow],
) -> bool:
    if not file_rows:
        return False

    pathspec = pathspec_from_root(repo_root, tracked_root)
    if git_tree_has_entries(repo_root, ref=from_ref, pathspec=pathspec):
        return False
    if not git_tree_has_entries(repo_root, ref=to_ref, pathspec=pathspec):
        return False
    return all(row.change_type == "A" and not row.old_path for row in file_rows)


def parse_name_status(output: str) -> dict[str, tuple[str, str, str]]:
    rows: dict[str, tuple[str, str, str]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        kind = status[:1]
        if kind in {"R", "C"} and len(parts) >= 3:
            old_path = parts[1].strip()
            new_path = parts[2].strip()
        elif len(parts) >= 2:
            old_path = ""
            new_path = parts[1].strip()
        else:
            continue
        rows[new_path or old_path] = (kind, old_path, new_path)
    return rows


def parse_numstat(output: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        insertions = parts[0].strip()
        deletions = parts[1].strip()
        path = parts[-1].strip()
        rows[path] = (insertions, deletions)
    return rows


def extract_bundle_fields(path_text: str) -> tuple[str, str, str, str, str, str]:
    pure = PurePosixPath(path_text)
    parts = pure.parts
    try:
        if "_build" in parts:
            root_idx = parts.index("_build")
            model = parts[root_idx + 1]
            region = parts[root_idx + 2]
            artifact = parts[root_idx + 3]
            tail = parts[root_idx + 4 :]
        elif "_review" in parts:
            root_idx = parts.index("_review")
            model = parts[root_idx + 1]
            region = parts[root_idx + 2]
            artifact = "review"
            tail = parts[root_idx + 3 :]
        else:
            return "", "", "", "", pure.name, pure.stem
    except IndexError:
        return "", "", "", "", pure.name, pure.stem

    section = tail[0] if len(tail) > 1 else ""
    file_name = pure.name
    page_key = PurePosixPath(file_name).stem
    relative_path = "/".join(tail) if tail else file_name
    return model, region, artifact, section, relative_path, page_key


def collect_diff_rows(
    *,
    repo_root: Path,
    tracked_root: Path,
    from_ref: str,
    to_ref: str,
) -> list[DiffRow]:
    pathspec = pathspec_from_root(repo_root, tracked_root)
    name_status = parse_name_status(
        run_git(
            ["diff", "--name-status", "--find-renames", from_ref, to_ref, "--", pathspec],
            cwd=repo_root,
        )
    )
    numstat = parse_numstat(
        run_git(
            ["diff", "--numstat", "--find-renames", from_ref, to_ref, "--", pathspec],
            cwd=repo_root,
        )
    )

    rows: list[DiffRow] = []
    for key in sorted(name_status):
        change_type, old_path, new_path = name_status[key]
        stats = numstat.get(new_path) or numstat.get(old_path) or ("", "")
        chosen_path = new_path or old_path
        model, region, artifact, section, relative_path, page_key = extract_bundle_fields(chosen_path)
        rows.append(
            DiffRow(
                tracked_root=pathspec,
                model=model,
                region=region,
                artifact=artifact,
                section=section,
                page_key=page_key,
                file_name=PurePosixPath(chosen_path).name,
                relative_path=relative_path,
                change_type=change_type,
                insertions=stats[0],
                deletions=stats[1],
                old_path=old_path,
                new_path=new_path or old_path,
                from_ref=from_ref,
                to_ref=to_ref,
            )
        )
    return rows


def git_show_text(repo_root: Path, *, ref: str, path_text: str) -> str:
    if not path_text:
        return ""
    try:
        return run_git(["show", f"{ref}:{path_text}"], cwd=repo_root)
    except subprocess.CalledProcessError:
        return ""


def build_report_base_name(tracked_root: Path, from_ref: str, to_ref: str) -> str:
    scope_name = tracked_root.name or "tracked_root"
    return f"{sanitize_token(scope_name)}_{sanitize_token(from_ref)}_to_{sanitize_token(to_ref)}"
