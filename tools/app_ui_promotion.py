"""Fail-closed contracts for reviewed App UI assets.

The source screenshots remain quarantined extraction evidence.  Each contract
below permits exactly its listed deterministic exports to enter bundles of one
model/region, and only for that contract's reviewed languages.  This is
intentionally not a generic "allow quarantine" switch: a new target needs its
own reviewed decision, carrier and pinned hashes.
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
# The JSON file is the reviewed contract carrier. Keep one immutable binding
# for the carrier itself while the legacy Python shadow remains in dual-read
# mode; this prevents semantically-irrelevant JSON edits from bypassing review.
PROMOTION_CONTRACT_SHA256 = (
    "c51ca6fc4177c3de37ce5cb7e46caae609d62f54b115122f061a3f9dcaf7e4b0"
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


@dataclass(frozen=True)
class ReviewedPromotion:
    """One reviewed decision: its carrier, bindings, candidates and exports."""

    promotion_id: str
    contract_path: Path
    contract_sha256: str
    reviewer: str
    decided_at: str
    models: tuple[str, ...]
    regions: tuple[str, ...]
    languages: tuple[str, ...]
    source: tuple[str, str]
    frozen_reference: tuple[str, str]
    recipe_path: Path
    recipe_sha256: str
    evidence_path: Path
    evidence_sha256: str
    candidates: tuple[CandidateSpec, ...]
    outputs: tuple[OutputSpec, ...]
    export_root: Path
    shared_prefix: str

    @property
    def label(self) -> str:
        return f"{'+'.join(self.models)}/{'+'.join(self.regions)}/{'+'.join(self.languages)}"

    @property
    def scope_payload(self) -> dict[str, list[str]]:
        return {
            "models": list(self.models),
            "regions": list(self.regions),
            "languages": list(self.languages),
        }

    @property
    def recipe_scope_payload(self) -> dict[str, list[str]]:
        return {
            "models": list(self.models),
            "regions": list(self.regions),
            "locales": list(self.languages),
        }

    @property
    def source_payload(self) -> dict[str, str]:
        return {"name": self.source[0], "sha256": self.source[1]}

    @property
    def reference_payload(self) -> dict[str, str]:
        return {"name": self.frozen_reference[0], "sha256": self.frozen_reference[1]}

    @property
    def candidate_asset_keys(self) -> tuple[str, ...]:
        return tuple(spec.asset_key for spec in self.candidates)

    @property
    def promoted_asset_keys(self) -> tuple[str, ...]:
        return tuple(spec.asset_key for spec in self.outputs)


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
# The US v1 names stay US-only: existing callers and tests read them as the
# original contract. Use ALL_PROMOTED_ASSET_KEYS / promotion_for_asset() for
# every reviewed contract.
PROMOTED_ASSET_KEYS = tuple(spec.asset_key for spec in PROMOTED_OUTPUTS)

US_PROMOTION = ReviewedPromotion(
    promotion_id=PROMOTION_ID,
    contract_path=PROMOTION_RELATIVE_PATH,
    contract_sha256=PROMOTION_CONTRACT_SHA256,
    reviewer=EXPECTED_REVIEWER,
    decided_at=EXPECTED_DECIDED_AT,
    models=("JE-1000F",),
    regions=("US",),
    languages=("en", "fr", "es"),
    source=(EXPECTED_SOURCE["name"], EXPECTED_SOURCE["sha256"]),
    frozen_reference=(EXPECTED_REFERENCE["name"], EXPECTED_REFERENCE["sha256"]),
    recipe_path=RECIPE_RELATIVE_PATH,
    recipe_sha256=EXPECTED_RECIPE_SHA256,
    evidence_path=EVIDENCE_RELATIVE_PATH,
    evidence_sha256=EXPECTED_EVIDENCE_SHA256,
    candidates=CANDIDATES,
    outputs=PROMOTED_OUTPUTS,
    export_root=PROMOTED_EXPORT_ROOT,
    shared_prefix="app/je1000f_us/",
)

# JE-1000F/EU: the EU/UK print (V2.0-2026-06-18) is both the extraction source
# and the frozen reference; its fr/es/de/it blocks print the same English App
# screens as the EN block. Each export is its evidence crop byte for byte (one
# full-canvas placement); the printed captions stay native text.
EU_PROMOTION_ID = "je1000f-eu-app-ui-v1"
EU_EXPORT_ROOT = word_common_assets_of(Path(PathSegments.DOCS)) / "app" / "je1000f_eu"
_EU_SOURCE = (
    "Jackery Explorer 1000 User Manual (JE-1000F) V2.0 EU-UK-2026-06-18.pdf",
    "0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe",
)
_EU_CANDIDATES = (
    CandidateSpec(
        "app/je1000f_eu/english_ui/add_device_screens",
        Path("data/asset_evidence/app_ui/je1000f_eu/pdf-p21-add-device.png"),
        "02f840f1341d94d08478c84ea4ae88280ef2806d618484596885efbe4debafe0",
        (706, 618),
    ),
    CandidateSpec(
        "app/je1000f_eu/english_ui/connect_result_screens",
        Path("data/asset_evidence/app_ui/je1000f_eu/pdf-p22-connect-result.png"),
        "23cde742b3012b96fce07f9efe3475ee2e75230f2b2d39311291a33d4cf51f69",
        (1072, 606),
    ),
)
EU_PROMOTION = ReviewedPromotion(
    promotion_id=EU_PROMOTION_ID,
    contract_path=Path(PathSegments.DATA) / "asset_promotions" / "je1000f_eu_app_ui_v1.json",
    contract_sha256="4f8bafbad787355f64db5deceac70778fa74b30a661fc4a2eca4f4b1a96834b2",
    reviewer="唐夏冰",
    decided_at="2026-09-24T06:18:00-07:00",
    models=("JE-1000F",),
    regions=("EU",),
    languages=("en", "fr", "es", "de", "it", "uk"),
    source=_EU_SOURCE,
    frozen_reference=_EU_SOURCE,
    recipe_path=Path(PathSegments.DATA) / "asset_recipes" / "manual_je1000f_eu_app_ui.json",
    recipe_sha256="feac8187a82c298db2a297bf8469a9814fbc0b758ccf4d34a6642852c3adcd47",
    evidence_path=Path(PathSegments.DATA) / "asset_evidence" / "app_ui_candidates_je1000f_eu.json",
    evidence_sha256="f3431b131848856c997bbcb79c61d5dd7556d81d1b6c1cbf8d2ca2b2cb5645a6",
    candidates=_EU_CANDIDATES,
    outputs=(
        OutputSpec(
            "app/je1000f_eu/add_device",
            EU_EXPORT_ROOT / "add_device_je1000f_eu.png",
            _EU_CANDIDATES[0].sha256,
            _EU_CANDIDATES[0].dimensions_px,
            (PlacementSpec(_EU_CANDIDATES[0].asset_key, (0, 0), (0, 0, 706, 618)),),
        ),
        OutputSpec(
            "app/je1000f_eu/connect_result",
            EU_EXPORT_ROOT / "connect_result_je1000f_eu.png",
            _EU_CANDIDATES[1].sha256,
            _EU_CANDIDATES[1].dimensions_px,
            (PlacementSpec(_EU_CANDIDATES[1].asset_key, (0, 0), (0, 0, 1072, 606)),),
        ),
    ),
    export_root=EU_EXPORT_ROOT,
    shared_prefix="app/je1000f_eu/",
)

REVIEWED_PROMOTIONS = (US_PROMOTION, EU_PROMOTION)
_PROMOTIONS_BY_ID = {promotion.promotion_id: promotion for promotion in REVIEWED_PROMOTIONS}
_PROMOTIONS_BY_ASSET = {
    asset_key: promotion
    for promotion in REVIEWED_PROMOTIONS
    for asset_key in promotion.promoted_asset_keys
}
ALL_PROMOTED_ASSET_KEYS = tuple(_PROMOTIONS_BY_ASSET)

_RAW_LATEX_ALIASES = {
    "add_device.png": "asset:app/add_device",
    "connect_result.png": "asset:app/connect_result",
}
_PROMOTION_MARKER_RE = re.compile(r"(?:^|[\s;；])reviewed-promotion=([a-z0-9-]+)(?=$|[\s;；])")


def promotion_for_asset(asset_key: str) -> ReviewedPromotion | None:
    """Return the reviewed contract that owns one promoted export key."""

    return _PROMOTIONS_BY_ASSET.get(asset_key)


def reviewed_app_uri_for_raw_latex(
    raw_value: str,
    *,
    model: str | None,
    region: str | None,
    language: str | None,
) -> str | None:
    """Map legacy raw-LaTeX basenames only inside a reviewed target."""

    target = (
        (model or "").strip().upper(),
        (region or "").strip().upper(),
        (language or "").strip().casefold(),
    )
    if not any(
        target[0] in promotion.models
        and target[1] in promotion.regions
        and target[2] in promotion.languages
        for promotion in REVIEWED_PROMOTIONS
    ):
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


def _validate_decision_and_bindings(
    promotion: ReviewedPromotion,
    payload: dict[str, Any],
    repo_root: Path,
) -> None:
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
    if payload["promotion_id"] != promotion.promotion_id:
        raise ReviewedPromotionError("promotion_id does not match the immutable promotion")

    decision = payload["decision"]
    if not isinstance(decision, dict):
        raise ReviewedPromotionError("promotion decision must be an object")
    _expect_keys(decision, {"reviewer", "decided_at", "outcome"}, label="decision")
    if decision["reviewer"] != promotion.reviewer:
        raise ReviewedPromotionError(f"promotion reviewer must be {promotion.reviewer}")
    if decision["outcome"] != "approved":
        raise ReviewedPromotionError("promotion decision outcome must be approved")
    try:
        decided_at = datetime.fromisoformat(str(decision["decided_at"]))
    except ValueError as exc:
        raise ReviewedPromotionError("promotion decision time is not ISO-8601") from exc
    if decided_at.tzinfo is None or decided_at.utcoffset() is None:
        raise ReviewedPromotionError("promotion decision time must include a timezone")
    if str(decision["decided_at"]) != promotion.decided_at:
        raise ReviewedPromotionError("promotion decision time does not match the reviewed decision")
    if payload["scope"] != promotion.scope_payload:
        raise ReviewedPromotionError(f"promotion scope must be exactly {promotion.label}")

    bindings = payload["bindings"]
    if not isinstance(bindings, dict):
        raise ReviewedPromotionError("promotion bindings must be an object")
    _expect_keys(
        bindings,
        {"source", "frozen_reference", "recipe", "evidence"},
        label="bindings",
    )
    if bindings["source"] != promotion.source_payload:
        raise ReviewedPromotionError("promotion source binding does not match the reviewed source")
    if bindings["frozen_reference"] != promotion.reference_payload:
        raise ReviewedPromotionError(
            "promotion frozen reference binding does not match the reviewed reference"
        )
    expected_files = (
        ("recipe", promotion.recipe_path, promotion.recipe_sha256),
        ("evidence", promotion.evidence_path, promotion.evidence_sha256),
    )
    for label, relative, digest in expected_files:
        if bindings[label] != {"path": relative.as_posix(), "sha256": digest}:
            raise ReviewedPromotionError(f"promotion {label} binding is not immutable")
        _verify_file(repo_root, relative, digest, label=label)


def _validate_candidate_bindings(
    promotion: ReviewedPromotion,
    payload: dict[str, Any],
    repo_root: Path,
) -> None:
    candidates = promotion.candidates
    if payload["candidate_asset_key_whitelist"] != list(promotion.candidate_asset_keys):
        raise ReviewedPromotionError("candidate asset key whitelist is not exact")
    rows = payload["candidate_assets"]
    if not isinstance(rows, list) or len(rows) != len(candidates):
        raise ReviewedPromotionError(
            f"candidate whitelist must contain exactly {len(candidates)} assets"
        )
    for row, spec in zip(rows, candidates, strict=True):
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
    evidence = _load_json(repo_root / promotion.evidence_path, label="evidence")
    if evidence.get("evidence_status") != "quarantine":
        raise ReviewedPromotionError("candidate evidence must remain quarantine")
    if evidence.get("source") != promotion.source_payload:
        raise ReviewedPromotionError("candidate evidence source binding drifted")
    if evidence.get("frozen_reference") != promotion.reference_payload:
        raise ReviewedPromotionError("candidate evidence reference binding drifted")
    evidence_rows = evidence.get("candidates")
    if not isinstance(evidence_rows, list) or len(evidence_rows) != len(candidates):
        raise ReviewedPromotionError("candidate evidence whitelist is not exact")
    for row, spec in zip(evidence_rows, candidates, strict=True):
        if not isinstance(row, dict) or (
            row.get("asset_key") != spec.asset_key
            or row.get("output_path") != spec.path.as_posix()
            or row.get("output_sha256") != spec.sha256
            or row.get("output_dimensions_px") != list(spec.dimensions_px)
        ):
            raise ReviewedPromotionError(f"candidate evidence mismatch: {spec.asset_key}")
    recipe = _load_json(repo_root / promotion.recipe_path, label="recipe")
    recipe_rows = recipe.get("assets")
    if not isinstance(recipe_rows, list):
        raise ReviewedPromotionError("recipe assets must be a list")
    by_key = {
        row.get("asset_key"): row
        for row in recipe_rows
        if isinstance(row, dict) and isinstance(row.get("asset_key"), str)
    }
    for spec in candidates:
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
            or row.get("scope") != promotion.recipe_scope_payload
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


def _output_payload(spec: OutputSpec) -> dict[str, Any]:
    return {
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


def _validate_output_bindings(
    promotion: ReviewedPromotion,
    payload: dict[str, Any],
    repo_root: Path,
) -> None:
    outputs = promotion.outputs
    if payload["promoted_asset_key_whitelist"] != list(promotion.promoted_asset_keys):
        raise ReviewedPromotionError("promoted output whitelist is not exact")
    rows = payload["promoted_outputs"]
    if not isinstance(rows, list) or len(rows) != len(outputs):
        raise ReviewedPromotionError(
            f"promoted output whitelist must contain exactly {len(outputs)} assets"
        )
    for row, spec in zip(rows, outputs, strict=True):
        if not isinstance(row, dict):
            raise ReviewedPromotionError("promoted output entry must be an object")
        _expect_keys(
            row,
            {"asset_key", "path", "sha256", "dimensions_px", "composition"},
            label="promoted output",
        )
        if row != _output_payload(spec):
            raise ReviewedPromotionError(f"promoted output binding mismatch: {spec.asset_key}")
        path = _verify_file(repo_root, spec.path, spec.sha256, label=f"output {spec.asset_key}")
        if _png_dimensions(path, label=f"output {spec.asset_key}") != spec.dimensions_px:
            raise ReviewedPromotionError(f"output dimensions mismatch: {spec.asset_key}")


def contract_payload(promotion: ReviewedPromotion) -> dict[str, Any]:
    """Return the carrier JSON a reviewed contract must match exactly."""

    return {
        "schema_version": "reviewed-asset-promotion/v1",
        "promotion_id": promotion.promotion_id,
        "decision": {
            "reviewer": promotion.reviewer,
            "decided_at": promotion.decided_at,
            "outcome": "approved",
        },
        "scope": promotion.scope_payload,
        "bindings": {
            "source": promotion.source_payload,
            "frozen_reference": promotion.reference_payload,
            "recipe": {
                "path": promotion.recipe_path.as_posix(),
                "sha256": promotion.recipe_sha256,
            },
            "evidence": {
                "path": promotion.evidence_path.as_posix(),
                "sha256": promotion.evidence_sha256,
            },
        },
        "candidate_asset_key_whitelist": list(promotion.candidate_asset_keys),
        "promoted_asset_key_whitelist": list(promotion.promoted_asset_keys),
        "candidate_assets": [
            {
                "asset_key": spec.asset_key,
                "path": spec.path.as_posix(),
                "sha256": spec.sha256,
                "dimensions_px": list(spec.dimensions_px),
            }
            for spec in promotion.candidates
        ],
        "promoted_outputs": [_output_payload(spec) for spec in promotion.outputs],
    }


def _validate_json_legacy_parity(promotion: ReviewedPromotion, payload: dict[str, Any]) -> None:
    if payload != contract_payload(promotion):
        raise ReviewedPromotionError(
            "promotion JSON/legacy contract parity mismatch; review the JSON carrier"
        )


def _validate_registry_record(promotion: ReviewedPromotion, record: RegistryRecordLike) -> None:
    by_key = {spec.asset_key: spec for spec in promotion.outputs}
    spec = by_key.get(record.asset_key)
    if spec is None:
        raise ReviewedPromotionError("registry asset is outside the promoted output whitelist")
    markers = _PROMOTION_MARKER_RE.findall(record.notes)
    if markers != [promotion.promotion_id]:
        raise ReviewedPromotionError("registry promotion marker is missing or does not match")
    if record.category != "插图" or record.textless_pending:
        raise ReviewedPromotionError("registry category/textless flags do not match the promotion")
    if record.status != "✅成品":
        raise ReviewedPromotionError("registry status must be approved")
    if record.language_dimension != "按语言":
        raise ReviewedPromotionError("registry language dimension must be 按语言")
    if record.model_scope != promotion.models:
        raise ReviewedPromotionError(
            f"registry model scope must be exactly {','.join(promotion.models)}"
        )
    if record.region_scope != promotion.regions:
        raise ReviewedPromotionError(
            f"registry region scope must be exactly {','.join(promotion.regions)}"
        )
    expected_base_key = record.asset_key.replace(promotion.shared_prefix, "app/", 1)
    if record.override_for != expected_base_key:
        raise ReviewedPromotionError("registry override target does not match the shared key")
    if record.language_variants != promotion.languages:
        raise ReviewedPromotionError(
            f"registry language variants must be exactly {','.join(promotion.languages)}"
        )
    if record.export_root != promotion.export_root:
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
    """Validate one immutable decision and optionally one registry binding."""

    promotion = _PROMOTIONS_BY_ID.get(promotion_id)
    if promotion is None:
        raise ReviewedPromotionError("promotion id is not on the immutable whitelist")
    contract_path = _safe_file(
        repo_root,
        promotion.contract_path,
        label="promotion contract",
    )
    payload = _load_json(contract_path, label="promotion contract")
    _validate_decision_and_bindings(promotion, payload, repo_root)
    _validate_candidate_bindings(promotion, payload, repo_root)
    _validate_output_bindings(promotion, payload, repo_root)
    _validate_json_legacy_parity(promotion, payload)
    if _sha256(contract_path) != promotion.contract_sha256:
        raise ReviewedPromotionError(
            "promotion contract SHA-256 does not match the reviewed carrier"
        )
    if registry_record is not None:
        _validate_registry_record(promotion, registry_record)
    return promotion.promotion_id


__all__ = (
    "ALL_PROMOTED_ASSET_KEYS",
    "CANDIDATE_ASSET_KEYS",
    "EU_PROMOTION",
    "EU_PROMOTION_ID",
    "PROMOTED_ASSET_KEYS",
    "PROMOTION_ID",
    "PROMOTION_CONTRACT_SHA256",
    "PROMOTION_RELATIVE_PATH",
    "REVIEWED_PROMOTIONS",
    "ReviewedPromotion",
    "ReviewedPromotionError",
    "US_PROMOTION",
    "contract_payload",
    "promotion_for_asset",
    "reviewed_app_uri_for_raw_latex",
    "validate_reviewed_promotion",
)
