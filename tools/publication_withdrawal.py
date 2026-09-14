"""Explicit local publication actions, reusing the frozen assembly contract."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from tools.publish_locale_identity import source_root, stored_targets, write_stored_payload
from tools.safe_copy import assert_source_tree_no_symlinks
from tools.utils.path_utils import PathSegments

SCHEMA = "web-publication-actions/v1"
LEDGER_NAME = "publication_actions.json"
_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REF = re.compile(r"[0-9a-f]{40}")


def _key(payload: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(payload[field]).casefold() for field in ("model", "region", "lang", "version"))


def manifest_sha256(output_dir: Path) -> str:
    return hashlib.sha256((output_dir / "publish_manifest.json").read_bytes()).hexdigest()


def _source_digest(root: Path) -> str:
    assert_source_tree_no_symlinks(root, label="publication restore source")
    inventory = [(p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
                 for p in sorted(root.rglob("*")) if p.is_file()]
    return hashlib.sha256(json.dumps(inventory, separators=(",", ":")).encode()).hexdigest()


def _ledger_path(output_dir: Path) -> Path:
    return source_root(output_dir).parent / LEDGER_NAME


def publication_actions(output_dir: Path) -> list[dict[str, Any]]:
    path = _ledger_path(output_dir)
    if path.is_symlink():
        raise RuntimeError("publication action ledger cannot be a symlink")
    if not path.exists():
        return []
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
        if ledger["schema_version"] != SCHEMA or not isinstance(ledger["actions"], list):
            raise ValueError("unsupported action ledger")
        states: dict[tuple[str, ...], str] = {}
        for event in ledger["actions"]:
            if event["action"] not in {"withdraw", "restore"}:
                raise ValueError("unsupported publication action")
            for field in ("model", "region", "lang", "version"):
                if not isinstance(event[field], str) or not _SEGMENT.fullmatch(event[field]):
                    raise ValueError("unsafe publication action identity")
            for field in ("operator", "reason", "recorded_at", "source_digest"):
                if not isinstance(event[field], str) or not event[field].strip():
                    raise ValueError("incomplete publication action")
            for field in ("before_ref", "restore_ref"):
                if not _REF.fullmatch(event[field]):
                    raise ValueError("action requires pinned Git refs")
            for route in event["notice_routes"]:
                if (not isinstance(route, str) or not route.endswith(".md")
                        or any(not _SEGMENT.fullmatch(part) for part in route.split("/"))):
                    raise ValueError("unsafe withdrawal notice route")
            key = _key(event)
            previous = states.get(key)
            if (event["action"] == "restore" and previous != "withdraw") or (
                event["action"] == "withdraw" and previous == "withdraw"
            ):
                raise ValueError("invalid publication action transition")
            states[key] = event["action"]
        return ledger["actions"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(f"invalid publication action ledger: {path}") from exc


def _withdrawn(output_dir: Path) -> dict[tuple[str, ...], dict[str, Any]]:
    latest = {_key(event): event for event in publication_actions(output_dir)}
    return {key: event for key, event in latest.items() if event["action"] == "withdraw"}


def reject_withdrawn_version(output_dir: Path, *, model: str, region: str, lang: str, version: str) -> None:
    identity = tuple(value.casefold() for value in (model, region, lang, version))
    if identity in _withdrawn(output_dir):
        raise RuntimeError(f"withdrawn publication requires explicit restoration: {'/'.join(identity)}")


def write_withdrawal_notices(output_dir: Path) -> None:
    active = {_key(payload)[:3] for _, payload in stored_targets(output_dir)}
    for identity, event in _withdrawn(output_dir).items():
        if identity[:3] in active:
            continue  # A different approved version owns the canonical route.
        for relative in event["notice_routes"]:
            path = output_dir / PathSegments.WEB / relative
            if path.exists():
                continue  # Preserve a surviving language's default/alias route.
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "---\norphan: true\n---\n\n# Publication withdrawn\n\n"
                "This publication has been withdrawn. Please use the manual center "
                "to find an available publication.\n", encoding="utf-8",
            )


def _notice_routes(payload: dict[str, Any]) -> list[str]:
    route = Path(payload["route"])
    names = [payload["manual"], "index.md"]
    routes = [(route / name).as_posix() for name in names]
    routes.append(payload["manual"])  # RTD emits a root short alias for every locale.
    if payload.get("legacy_default"):
        legacy = Path(payload["legacy_route"])
        routes.append((legacy / "index.md").as_posix())
        for alias in payload["legacy_aliases"]:
            routes.extend([(legacy / f"{alias}.md").as_posix(), f"{alias}.md"])
    return sorted(set(routes))


def _routing(output_dir: Path, identity: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{"language": p["lang"], "route": p["route"], "manual": p["manual"],
             "legacy_route": p.get("legacy_route"), "legacy_aliases": p.get("legacy_aliases", []),
             "legacy_default": p.get("legacy_default")}
            for _, p in stored_targets(output_dir) if _key(p)[:2] == identity[:2]]


def _set_default(output_dir: Path, identity: tuple[str, ...], language: str | None) -> None:
    group = [(path, p) for path, p in stored_targets(output_dir) if _key(p)[:2] == identity[:2]]
    if not group:
        return
    defaults = [p for _, p in group if p.get("legacy_default") is True]
    if language is None:
        if len(defaults) != 1:
            raise RuntimeError("explicit default_language required for withdrawal/restoration")
        return
    if language.casefold() not in {p["lang"].casefold() for _, p in group}:
        raise RuntimeError("default_language must name a remaining publication")
    for path, payload in group:
        payload["legacy_default"] = payload["lang"].casefold() == language.casefold()
        write_stored_payload(path, payload)


def change_publication_state(
    *, output_dir: Path, action: str, model: str, region: str, lang: str,
    version: str, reason: str, operator: str, before_ref: str, restore_ref: str,
    expected_manifest_sha256: str, restore_snapshot: Path | None = None,
    default_language: str | None = None, title: str = "Auto Manual Library",
) -> dict[str, Any]:
    """Mutate only a local publish candidate; Git commits and deployment are external.

    Restoration accepts only the exact withdrawn source bytes. The before ref
    is externally verified by the caller; the manifest digest is its local
    compare-and-swap precondition. No new commit hash can be known here.
    """
    from tools import publish_branch_assembly as assembly

    if action not in {"withdraw", "restore"}:
        raise RuntimeError("action must be withdraw or restore")
    if any(not _SEGMENT.fullmatch(v) for v in (model, region, lang, version)):
        raise RuntimeError("unsafe publication action identity")
    if not reason.strip() or not operator.strip() or any(not _REF.fullmatch(v) for v in (before_ref, restore_ref)):
        raise RuntimeError("reason, operator and pinned before/restore refs are required")
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise RuntimeError("publication action requires an existing real publish directory")
    assert_source_tree_no_symlinks(output_dir, label="publication action source")
    output_dir = output_dir.resolve()
    if manifest_sha256(output_dir) != expected_manifest_sha256:
        raise RuntimeError("publication manifest changed; re-plan the action")
    events = publication_actions(output_dir)
    identity = tuple(v.casefold() for v in (model, region, lang, version))
    current = [(path, p) for path, p in stored_targets(output_dir) if _key(p)[:3] == identity[:3]]
    source: Path | None = None
    if action == "withdraw":
        if len(current) != 1 or _key(current[0][1]) != identity:
            raise RuntimeError("withdrawal must match the currently published version")
        if restore_ref != before_ref:
            raise RuntimeError("withdrawal restore_ref must pin the before snapshot")
        path, payload = current[0]
        digest = _source_digest(path.parent)
        notice_routes = _notice_routes(payload)
    else:
        if current:
            raise RuntimeError("restore cannot replace an active publication; plan a version update")
        prior = _withdrawn(output_dir).get(identity)
        if prior is None or restore_snapshot is None or restore_ref != prior["restore_ref"]:
            raise RuntimeError("restore requires a withdrawn version and its pinned snapshot")
        assert_source_tree_no_symlinks(restore_snapshot, label="publication restore snapshot")
        saved = [(path, p) for path, p in stored_targets(restore_snapshot) if _key(p) == identity]
        if len(saved) != 1 or _source_digest(saved[0][0].parent) != prior["source_digest"]:
            raise RuntimeError("restore snapshot does not match withdrawn source bytes")
        path, payload = saved[0]
        source, digest, notice_routes = path.parent, prior["source_digest"], prior["notice_routes"]
    event = dict(
        action=action, model=model, region=region, lang=lang, version=version,
        reason=reason.strip(), operator=operator.strip(), before_ref=before_ref,
        restore_ref=restore_ref, before_manifest_sha256=expected_manifest_sha256,
        source_ref=payload["git_ref"], source_digest=digest, notice_routes=notice_routes,
        old_route=payload["route"] if action == "withdraw" else None,
        new_route=payload["route"] if action == "restore" else None,
        routing_before=_routing(output_dir, identity),
        recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    with tempfile.TemporaryDirectory(prefix=f".{output_dir.name}-action-", dir=output_dir.parent) as tmp:
        candidate = Path(tmp) / output_dir.name
        shutil.copytree(output_dir, candidate)
        destination = source_root(candidate) / payload["route"]
        if action == "withdraw":
            shutil.rmtree(destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, destination)
        _set_default(candidate, identity, default_language)
        if not stored_targets(candidate):
            raise RuntimeError("withdrawal of the final publication requires a site-retirement plan")
        event["routing_after"] = _routing(candidate, identity)
        _ledger_path(candidate).write_text(json.dumps({"schema_version": SCHEMA, "actions": [*events, event]},
                                                     ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assembly.rebuild_web_source(output_dir=candidate, title=title)
        event["routing_after"] = _routing(candidate, identity)
        _ledger_path(candidate).write_text(json.dumps({"schema_version": SCHEMA, "actions": [*events, event]},
                                                     ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assembly._enforce_web_only_tree(candidate)
        assembly._write_publish_manifest(candidate)
        assembly._enforce_file_size_limit(candidate, max_file_size_mb=assembly.DEFAULT_MAX_FILE_SIZE_MB)
        if manifest_sha256(output_dir) != expected_manifest_sha256:
            raise RuntimeError("publication manifest changed before promotion")
        assembly._promote_candidate(candidate=candidate, output_dir=output_dir)
    return {"schema_version": "web-publication-action-receipt/v1", "event": event,
            "candidate_manifest_sha256": manifest_sha256(output_dir),
            "candidate_ref": None, "deployed_ref": None}
