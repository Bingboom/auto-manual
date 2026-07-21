"""Fail-closed contract for the reviewed JE-1000F US App UI assets.

The source screenshots remain quarantined extraction evidence.  This module
permits exactly two deterministic composites to enter a JE-1000F/US bundle,
and only for the three reviewed languages.  It is intentionally not a generic
"allow quarantine" switch.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from tools.utils.path_utils import PathSegments, word_common_assets_of

PROMOTION_ID = "je1000f-us-app-ui-v1"
PROMOTION_RELATIVE_PATH = (
    Path(PathSegments.DATA)
    / "asset_promotions"
    / "je1000f_us_app_ui_v1.json"
)
RECIPE_RELATIVE_PATH = (
    Path(PathSegments.DATA)
    / "asset_recipes"
    / "manual_je1000f_us_master.json"
)
EVIDENCE_RELATIVE_PATH = (
    Path(PathSegments.DATA)
    / "asset_evidence"
    / "app_ui_candidates.json"
)
PROMOTED_EXPORT_ROOT = (
    word_common_assets_of(Path(PathSegments.DOCS))
    / "app"
    / "je1000f_us"
)

EXPECTED_REVIEWER = "唐夏冰"
EXPECTED_DECIDED_AT = "2026-07-20T09:50:46-07:00"
EXPECTED_SCOPE = {
    "models": ["JE-1000F"],
    "regions": ["US"],
    "languages": ["en", "fr", "es"],
}
EXPECTED_RECIPE_SCOPE = {
    "models": ["JE-1000F"],
    "regions": ["US"],
    "locales": ["en", "fr", "es"],
}
EXPECTED_SOURCE = {
    "name": "16-0102-000404 说明书 HTE1531000A-US-JAK RoHS REACH.ai",
    "sha256": "ee1fd9367021c99b3a16e14dc8aa702929c71ac4c98c7132816da05d90ce06ed",
}
EXPECTED_REFERENCE = {
    "name": "Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf",
    "sha256": "e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2",
}
EXPECTED_RECIPE_SHA256 = (
    "19719f2c2b78265cfc6563c17c79872668ae65b2011a3fda84a0b4f074bffcb7"
)
EXPECTED_EVIDENCE_SHA256 = (
    "d821ead5e7cabb949294ec0a27d6a63b48ec17ce5f45f176e1521682d40f88a0"
)


class ReviewedPromotionError(RuntimeError):
    """Raised when the reviewed promotion or one of its bindings drifts."""


class RegistryRecordLike(Protocol):
    asset_key: str
    override_for: str | None
    category: str
    language_dimension: str
    status: str
    textless_pending: bool
    model_scope: tuple[str, ...]
    region_scope: tuple[str, ...]
    export_root: Path | None
    language_variants: tuple[str, ...]
    hashes: tuple[tuple[str, str], ...]
    notes: str


@dataclass(frozen=True)
class CandidateSpec:
    asset_key: str
    path: Path
    sha256: str
    dimensions_px: tuple[int, int]


@dataclass(frozen=True)
class PlacementSpec:
    candidate_asset_key: str
    xy_px: tuple[int, int]
    source_rect_px: tuple[int, int, int, int]


@dataclass(frozen=True)
class OutputSpec:
    asset_key: str
    path: Path
    sha256: str
    dimensions_px: tuple[int, int]
    placements: tuple[PlacementSpec, ...]


CANDIDATES = (
    CandidateSpec(
        "app/je1000f_us/english_ui/add_device_home",
        Path("data/asset_evidence/app_ui/je1000f_us/ai-p39-add-device-home.png"),
        "5b68f2e13b4afe6fa4302ce4b6160ec64f0f7b3799e05a2a4db6ed41ea796005",
        (278, 601),
    ),
    CandidateSpec(
        "app/je1000f_us/english_ui/bluetooth_configuration",
        Path("data/asset_evidence/app_ui/je1000f_us/ai-p39-bluetooth-configuration.png"),
        "7d78debeed59a9076758635aefc8cb1056e6c71142a3b68b20e640c4c6ac934c",
        (277, 599),
    ),
    CandidateSpec(
        "app/je1000f_us/english_ui/device_scan",
        Path("data/asset_evidence/app_ui/je1000f_us/ai-p40-device-scan.png"),
        "4fc752f20312b665f84963258593960e44eb0c205686c46696e6a579ca142d4c",
        (272, 588),
    ),
    CandidateSpec(
        "app/je1000f_us/english_ui/wifi_configuration",
        Path("data/asset_evidence/app_ui/je1000f_us/ai-p40-wifi-configuration.png"),
        "1a22c0ccf6ce3f2827e6eb1f5e1a547f0daba8474d5ab95d66a4f5cecafa481e",
        (272, 587),
    ),
    CandidateSpec(
        "app/je1000f_us/english_ui/device_dashboard",
        Path("data/asset_evidence/app_ui/je1000f_us/ai-p40-device-dashboard.png"),
        "816b6059fe5493ee6b9a2c3915e5b542799e47ba61160509ea81f351e539d02a",
        (272, 651),
    ),
)
CANDIDATE_ASSET_KEYS = tuple(spec.asset_key for spec in CANDIDATES)

PROMOTED_OUTPUTS = (
    OutputSpec(
        "app/je1000f_us/add_device",
        PROMOTED_EXPORT_ROOT / "add_device_je1000f_us.png",
        "90ca2154225543ebddbd91dc49ca66ba6d4534180c54d6d4d6e8c6502efeda24",
        (680, 601),
        (
            PlacementSpec(CANDIDATE_ASSET_KEYS[0], (0, 0), (0, 0, 278, 601)),
            PlacementSpec(CANDIDATE_ASSET_KEYS[1], (403, 0), (0, 0, 277, 599)),
        ),
    ),
    OutputSpec(
        "app/je1000f_us/connect_result",
        PROMOTED_EXPORT_ROOT / "connect_result_je1000f_us.png",
        "50eca58b0f33d54f42f0efd137a79d457d66ff9a886b1c962c2a22aab044b7ec",
        (1046, 651),
        (
            PlacementSpec(CANDIDATE_ASSET_KEYS[2], (0, 4), (0, 0, 272, 588)),
            PlacementSpec(CANDIDATE_ASSET_KEYS[3], (387, 3), (0, 0, 272, 587)),
            # The evidence crop also contains the page's printed "2.5"
            # below the phone.  Keep that caption native by excluding it.
            PlacementSpec(CANDIDATE_ASSET_KEYS[4], (774, 0), (0, 0, 272, 600)),
        ),
    ),
)
PROMOTED_ASSET_KEYS = tuple(spec.asset_key for spec in PROMOTED_OUTPUTS)

_RAW_LATEX_ALIASES = {
    "add_device.png": "asset:app/add_device",
    "connect_result.png": "asset:app/connect_result",
}
_PROMOTION_MARKER_RE = re.compile(r"(?:^|[\s;；])reviewed-promotion=([a-z0-9-]+)(?=$|[\s;；])")


def reviewed_app_uri_for_raw_latex(
    raw_value: str,
    *,
    model: str | None,
    region: str | None,
    language: str | None,
) -> str | None:
    """Map legacy raw-LaTeX basenames only inside the reviewed target."""

    target = (
        (model or "").strip().upper(),
        (region or "").strip().upper(),
        (language or "").strip().casefold(),
    )
    if target[:2] != ("JE-1000F", "US") or target[2] not in {"en", "fr", "es"}:
        return None
    token = raw_value.strip()
    if token in _RAW_LATEX_ALIASES.values():
        return token
    return _RAW_LATEX_ALIASES.get(token)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ReviewedPromotionError(f"duplicate JSON field: {key}")
        out[key] = value
    return out


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_json_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewedPromotionError(f"{label} is not valid readable JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ReviewedPromotionError(f"{label} must be a JSON object")
    return payload


def _expect_keys(row: dict[str, Any], expected: set[str], *, label: str) -> None:
    if set(row) != expected:
        raise ReviewedPromotionError(
            f"{label} fields must be exactly {sorted(expected)}; found {sorted(row)}"
        )


def _safe_file(repo_root: Path, relative: Path, *, label: str) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ReviewedPromotionError(f"{label} path is unsafe: {relative}")
    root = repo_root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ReviewedPromotionError(f"{label} path must not use symlinks: {relative}")
    try:
        path = current.resolve(strict=True)
        path.relative_to(root)
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise ReviewedPromotionError(f"{label} file is missing or outside the repository") from exc
    if not path.is_file():
        raise ReviewedPromotionError(f"{label} path is not a file: {relative}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_file(
    repo_root: Path,
    relative: Path,
    expected_sha256: str,
    *,
    label: str,
) -> Path:
    path = _safe_file(repo_root, relative, label=label)
    if _sha256(path) != expected_sha256:
        raise ReviewedPromotionError(f"{label} SHA-256 does not match the reviewed binding")
    return path


def _png_dimensions(path: Path, *, label: str) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ReviewedPromotionError(f"{label} is not a valid PNG")
    return struct.unpack(">II", header[16:24])


def _validate_decision_and_bindings(payload: dict[str, Any], repo_root: Path) -> None:
    _expect_keys(
        payload,
        {
            "schema_version",
            "promotion_id",
            "decision",
            "scope",
            "bindings",
            "candidate_asset_key_whitelist",
            "promoted_asset_key_whitelist",
            "candidate_assets",
            "promoted_outputs",
        },
        label="promotion",
    )
    if payload["schema_version"] != "reviewed-asset-promotion/v1":
        raise ReviewedPromotionError("promotion schema_version is not supported")
    if payload["promotion_id"] != PROMOTION_ID:
        raise ReviewedPromotionError("promotion_id does not match the immutable promotion")

    decision = payload["decision"]
    if not isinstance(decision, dict):
        raise ReviewedPromotionError("promotion decision must be an object")
    _expect_keys(decision, {"reviewer", "decided_at", "outcome"}, label="decision")
    if decision["reviewer"] != EXPECTED_REVIEWER:
        raise ReviewedPromotionError("promotion reviewer must be 唐夏冰")
    if decision["outcome"] != "approved":
        raise ReviewedPromotionError("promotion decision outcome must be approved")
    try:
        decided_at = datetime.fromisoformat(str(decision["decided_at"]))
    except ValueError as exc:
        raise ReviewedPromotionError("promotion decision time is not ISO-8601") from exc
    if decided_at.tzinfo is None or decided_at.utcoffset() is None:
        raise ReviewedPromotionError("promotion decision time must include a timezone")
    if str(decision["decided_at"]) != EXPECTED_DECIDED_AT:
        raise ReviewedPromotionError("promotion decision time does not match the reviewed decision")
    if payload["scope"] != EXPECTED_SCOPE:
        raise ReviewedPromotionError("promotion scope must be exactly JE-1000F/US/en+fr+es")

    bindings = payload["bindings"]
    if not isinstance(bindings, dict):
        raise ReviewedPromotionError("promotion bindings must be an object")
    _expect_keys(
        bindings,
        {"source", "frozen_reference", "recipe", "evidence"},
        label="bindings",
    )
    if bindings["source"] != EXPECTED_SOURCE:
        raise ReviewedPromotionError("promotion source binding does not match the reviewed AI")
    if bindings["frozen_reference"] != EXPECTED_REFERENCE:
        raise ReviewedPromotionError("promotion frozen reference binding does not match the PDF")
    expected_files = (
        ("recipe", RECIPE_RELATIVE_PATH, EXPECTED_RECIPE_SHA256),
        ("evidence", EVIDENCE_RELATIVE_PATH, EXPECTED_EVIDENCE_SHA256),
    )
    for label, relative, digest in expected_files:
        if bindings[label] != {"path": relative.as_posix(), "sha256": digest}:
            raise ReviewedPromotionError(f"promotion {label} binding is not immutable")
        _verify_file(repo_root, relative, digest, label=label)


def _validate_candidate_bindings(payload: dict[str, Any], repo_root: Path) -> None:
    if payload["candidate_asset_key_whitelist"] != list(CANDIDATE_ASSET_KEYS):
        raise ReviewedPromotionError("candidate asset key whitelist is not exact")
    rows = payload["candidate_assets"]
    if not isinstance(rows, list) or len(rows) != len(CANDIDATES):
        raise ReviewedPromotionError("candidate whitelist must contain exactly five assets")
    for row, spec in zip(rows, CANDIDATES, strict=True):
        if not isinstance(row, dict):
            raise ReviewedPromotionError("candidate entry must be an object")
        _expect_keys(row, {"asset_key", "path", "sha256", "dimensions_px"}, label="candidate")
        expected = {
            "asset_key": spec.asset_key,
            "path": spec.path.as_posix(),
            "sha256": spec.sha256,
            "dimensions_px": list(spec.dimensions_px),
        }
        if row != expected:
            raise ReviewedPromotionError(f"candidate binding mismatch: {spec.asset_key}")
        path = _verify_file(repo_root, spec.path, spec.sha256, label=f"candidate {spec.asset_key}")
        if _png_dimensions(path, label=f"candidate {spec.asset_key}") != spec.dimensions_px:
            raise ReviewedPromotionError(f"candidate dimensions mismatch: {spec.asset_key}")

    evidence = _load_json(repo_root / EVIDENCE_RELATIVE_PATH, label="evidence")
    if evidence.get("evidence_status") != "quarantine":
        raise ReviewedPromotionError("candidate evidence must remain quarantine")
    if evidence.get("source") != EXPECTED_SOURCE:
        raise ReviewedPromotionError("candidate evidence source binding drifted")
    if evidence.get("frozen_reference") != EXPECTED_REFERENCE:
        raise ReviewedPromotionError("candidate evidence reference binding drifted")
    evidence_rows = evidence.get("candidates")
    if not isinstance(evidence_rows, list) or len(evidence_rows) != len(CANDIDATES):
        raise ReviewedPromotionError("candidate evidence whitelist is not exact")
    for row, spec in zip(evidence_rows, CANDIDATES, strict=True):
        if not isinstance(row, dict) or (
            row.get("asset_key") != spec.asset_key
            or row.get("output_path") != spec.path.as_posix()
            or row.get("output_sha256") != spec.sha256
            or row.get("output_dimensions_px") != list(spec.dimensions_px)
        ):
            raise ReviewedPromotionError(f"candidate evidence mismatch: {spec.asset_key}")

    recipe = _load_json(repo_root / RECIPE_RELATIVE_PATH, label="recipe")
    recipe_rows = recipe.get("assets")
    if not isinstance(recipe_rows, list):
        raise ReviewedPromotionError("recipe assets must be a list")
    by_key = {
        row.get("asset_key"): row
        for row in recipe_rows
        if isinstance(row, dict) and isinstance(row.get("asset_key"), str)
    }
    for spec in CANDIDATES:
        row = by_key.get(spec.asset_key)
        expected_output = {
            "format": "png",
            "path": spec.path.as_posix(),
            "scale": 4,
            "expected_sha256": spec.sha256,
        }
        if not isinstance(row, dict) or (
            row.get("build_eligible") is not False
            or row.get("visual_review_required") is not True
            or row.get("scope") != EXPECTED_RECIPE_SCOPE
            or not isinstance(row.get("gate"), dict)
            or row["gate"].get("status") != "quarantine"
            or row.get("outputs") != [expected_output]
        ):
            raise ReviewedPromotionError(
                f"recipe candidate must remain quarantined and hash-bound: {spec.asset_key}"
            )


def _placement_payload(spec: PlacementSpec) -> dict[str, Any]:
    return {
        "candidate_asset_key": spec.candidate_asset_key,
        "xy_px": list(spec.xy_px),
        "source_rect_px": list(spec.source_rect_px),
    }


def _validate_output_bindings(payload: dict[str, Any], repo_root: Path) -> None:
    if payload["promoted_asset_key_whitelist"] != list(PROMOTED_ASSET_KEYS):
        raise ReviewedPromotionError("promoted output whitelist is not exact")
    rows = payload["promoted_outputs"]
    if not isinstance(rows, list) or len(rows) != len(PROMOTED_OUTPUTS):
        raise ReviewedPromotionError("promoted output whitelist must contain exactly two assets")
    for row, spec in zip(rows, PROMOTED_OUTPUTS, strict=True):
        if not isinstance(row, dict):
            raise ReviewedPromotionError("promoted output entry must be an object")
        _expect_keys(
            row,
            {"asset_key", "path", "sha256", "dimensions_px", "composition"},
            label="promoted output",
        )
        expected = {
            "asset_key": spec.asset_key,
            "path": spec.path.as_posix(),
            "sha256": spec.sha256,
            "dimensions_px": list(spec.dimensions_px),
            "composition": {
                "canvas_px": list(spec.dimensions_px),
                "background": "#FFFFFF",
                "placements": [_placement_payload(item) for item in spec.placements],
            },
        }
        if row != expected:
            raise ReviewedPromotionError(f"promoted output binding mismatch: {spec.asset_key}")
        path = _verify_file(repo_root, spec.path, spec.sha256, label=f"output {spec.asset_key}")
        if _png_dimensions(path, label=f"output {spec.asset_key}") != spec.dimensions_px:
            raise ReviewedPromotionError(f"output dimensions mismatch: {spec.asset_key}")


def _validate_registry_record(record: RegistryRecordLike) -> None:
    by_key = {spec.asset_key: spec for spec in PROMOTED_OUTPUTS}
    spec = by_key.get(record.asset_key)
    if spec is None:
        raise ReviewedPromotionError("registry asset is outside the promoted output whitelist")
    markers = _PROMOTION_MARKER_RE.findall(record.notes)
    if markers != [PROMOTION_ID]:
        raise ReviewedPromotionError("registry promotion marker is missing or does not match")
    if record.category != "插图" or record.textless_pending:
        raise ReviewedPromotionError("registry category/textless flags do not match the promotion")
    if record.status != "✅成品":
        raise ReviewedPromotionError("registry status must be approved")
    if record.language_dimension != "按语言":
        raise ReviewedPromotionError("registry language dimension must be 按语言")
    if record.model_scope != ("JE-1000F",):
        raise ReviewedPromotionError("registry model scope must be exactly JE-1000F")
    if record.region_scope != ("US",):
        raise ReviewedPromotionError("registry region scope must be exactly US")
    expected_base_key = record.asset_key.replace("app/je1000f_us/", "app/", 1)
    if record.override_for != expected_base_key:
        raise ReviewedPromotionError("registry override target does not match the shared key")
    if record.language_variants != ("en", "fr", "es"):
        raise ReviewedPromotionError("registry language variants must be exactly en,fr,es")
    if record.export_root != PROMOTED_EXPORT_ROOT:
        raise ReviewedPromotionError("registry export root does not match the scoped promotion")
    expected_hashes = ((spec.path.name, spec.sha256),)
    if record.hashes != expected_hashes:
        raise ReviewedPromotionError("registry hash must be the exact full promoted output SHA-256")


def validate_reviewed_promotion(
    repo_root: Path,
    promotion_id: str,
    *,
    registry_record: RegistryRecordLike | None = None,
) -> str:
    """Validate the immutable decision and optionally one registry binding."""

    if promotion_id != PROMOTION_ID:
        raise ReviewedPromotionError("promotion id is not on the immutable whitelist")
    contract_path = _safe_file(
        repo_root,
        PROMOTION_RELATIVE_PATH,
        label="promotion contract",
    )
    payload = _load_json(contract_path, label="promotion contract")
    _validate_decision_and_bindings(payload, repo_root)
    _validate_candidate_bindings(payload, repo_root)
    _validate_output_bindings(payload, repo_root)
    if registry_record is not None:
        _validate_registry_record(registry_record)
    return PROMOTION_ID


__all__ = (
    "CANDIDATE_ASSET_KEYS",
    "PROMOTED_ASSET_KEYS",
    "PROMOTION_ID",
    "PROMOTION_RELATIVE_PATH",
    "ReviewedPromotionError",
    "reviewed_app_uri_for_raw_latex",
    "validate_reviewed_promotion",
)
