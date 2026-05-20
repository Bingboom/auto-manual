from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from tools.message_control_contract import (
    ACTION_BUILD_DRAFT_PACKAGE,
    ACTION_PUBLISH,
    ACTION_QUERY_STATUS,
    ACTION_START_REVIEW,
    STATUS_NEEDS_CONFIRMATION,
    STATUS_NEEDS_INPUT,
    STATUS_READY,
    STATUS_UNRESOLVED,
    MessageControlResolution,
    MessageControlRoute,
    MessageTargetSelector,
)
from tools.queue_config_resolution import config_family_id, normalize_build_family


def normalize_message_text(raw_message: str) -> str:
    return " ".join(str(raw_message or "").strip().split())


def detect_action(raw_message: str) -> str:
    text = normalize_message_text(raw_message).lower()
    patterns: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            ACTION_BUILD_DRAFT_PACKAGE,
            (
                r"\bbuild\s+draft\s+package\b",
                r"\bdraft\s+package\b",
                r"\bdraft\s+build\b",
                r"构建草稿包",
                r"草稿包",
                r"构建\s*draft",
                r"补跑",
                r"补构建",
                r"补触发",
                r"重跑",
                r"重新构建",
                r"重试",
            ),
        ),
        (
            ACTION_START_REVIEW,
            (
                r"\bstart\s+review\b",
                r"\bcreate\s+review\b",
                r"\benter\s+review\b",
                r"进入\s*review",
                r"开始\s*review",
                r"发起\s*review",
            ),
        ),
        (
            ACTION_PUBLISH,
            (
                r"\bpublish\b",
                r"\brelease\b",
                r"正式发布",
                r"发布",
            ),
        ),
        (
            ACTION_QUERY_STATUS,
            (
                r"\blatest\s+status\b",
                r"\bstatus\b",
                r"\bstate\b",
                r"查询状态",
                r"查状态",
                r"状态",
                r"进度",
                r"好了没",
                r"好了",
                r"到哪",
                r"查不到",
                r"找不到",
            ),
        ),
    )
    for action, action_patterns in patterns:
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in action_patterns):
            return action
    return ""


def collect_family_config_map(
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
) -> dict[str, tuple[Path, ...]]:
    mapping: dict[str, list[Path]] = {}
    for config_path in sorted(repo_root.glob("config*.yaml")):
        try:
            cfg = config_loader(config_path)
        except RuntimeError:
            continue
        family_id = normalize_build_family(config_family_id(cfg))
        if not family_id:
            continue
        mapping.setdefault(family_id, []).append(config_path)
    return {key: tuple(paths) for key, paths in mapping.items()}


def _compact_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _unique_preserve_order(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)


def extract_build_family(raw_message: str, known_families: tuple[str, ...]) -> str:
    text = normalize_message_text(raw_message).lower()
    compact_text = _compact_token(text)
    matches: list[str] = []
    for family in known_families:
        family_text = family.lower()
        family_compact = _compact_token(family_text)
        if re.search(rf"(?<![a-z0-9]){re.escape(family_text)}(?![a-z0-9])", text):
            matches.append(family)
            continue
        if family_compact and family_compact in compact_text:
            matches.append(family)
    unique_matches = _unique_preserve_order(matches)
    if len(unique_matches) == 1:
        return unique_matches[0]
    return ""


def _extract_first_group(patterns: tuple[str, ...], raw_message: str, *, flags: int = 0) -> str:
    for pattern in patterns:
        match = re.search(pattern, raw_message, flags=flags)
        if match:
            return str(match.group(1) or "").strip()
    return ""


def extract_selector_from_message(raw_message: str, known_families: tuple[str, ...]) -> MessageTargetSelector:
    record_id = _extract_first_group((r"\b(rec[a-z0-9]+)\b",), raw_message, flags=re.IGNORECASE).lower()
    document_key = _extract_first_group(
        (r"\b([A-Za-z]{1,6}-\d{3,5}[A-Za-z]?_[A-Za-z]{2}(?:_[A-Za-z]{2})?)\b",),
        raw_message,
        flags=re.IGNORECASE,
    )
    model = _extract_first_group((r"\b([A-Za-z]{1,6}-\d{3,5}[A-Za-z]?)\b",), raw_message, flags=re.IGNORECASE)
    region = _extract_first_group((r"\b(US|JP|CN|EU)\b",), raw_message, flags=re.IGNORECASE).upper()
    document_id = _extract_first_group(
        (
            r"\bdocument(?:_id)?\s+([A-Za-z0-9._/-]+)\b",
            r"\bdoc\s+([A-Za-z0-9._/-]+)\b",
            r"文档\s*([A-Za-z0-9._/-]+)\b",
        ),
        raw_message,
        flags=re.IGNORECASE,
    )
    git_ref = _extract_first_group(
        (
            r"\bfrom\s+branch\s+([A-Za-z0-9._/-]+)\b",
            r"\bbranch\s+([A-Za-z0-9._/-]+)\b",
            r"\bgit[_ -]?ref\s+([A-Za-z0-9._/-]+)\b",
            r"分支\s*([A-Za-z0-9._/-]+)\b",
        ),
        raw_message,
        flags=re.IGNORECASE,
    )
    version = _extract_first_group(
        (
            r"\bversion\s*([Vv]?\d+(?:\.\d+)*)\b",
            r"\bver\s*([Vv]?\d+(?:\.\d+)*)\b",
            r"版本\s*([Vv]?\d+(?:\.\d+)*)\b",
        ),
        raw_message,
        flags=re.IGNORECASE,
    )
    build_family = extract_build_family(raw_message, known_families)
    lang = ""
    if document_key:
        parts = document_key.split("_")
        if len(parts) >= 2:
            model = model or parts[0]
            region = region or parts[1].upper()
        if len(parts) >= 3:
            lang = parts[2].lower()
    return MessageTargetSelector(
        record_id=record_id,
        document_id=document_id,
        document_key=document_key,
        model=model,
        region=region,
        lang=lang,
        build_family=build_family,
        git_ref=git_ref,
        version=version,
    )


def merge_selector(
    extracted: MessageTargetSelector,
    *,
    record_id: str = "",
    document_id: str = "",
    document_key: str = "",
    model: str = "",
    region: str = "",
    lang: str = "",
    build_family: str = "",
    git_ref: str = "",
    version: str = "",
) -> tuple[MessageTargetSelector, tuple[str, ...]]:
    warnings: list[str] = []

    def pick(field_name: str, extracted_value: str, override_value: str) -> str:
        raw_override = str(override_value or "").strip()
        if not raw_override:
            return extracted_value
        if extracted_value and extracted_value != raw_override:
            warnings.append(f"{field_name}_overridden")
        return raw_override

    merged = MessageTargetSelector(
        record_id=pick("record_id", extracted.record_id, str(record_id or "").strip().lower()),
        document_id=pick("document_id", extracted.document_id, document_id.strip()),
        document_key=pick("document_key", extracted.document_key, document_key.strip()),
        model=pick("model", extracted.model, model.strip()),
        region=pick("region", extracted.region, region.strip().upper()),
        lang=pick("lang", extracted.lang, lang.strip().lower()),
        build_family=pick("build_family", extracted.build_family, normalize_build_family(build_family)),
        git_ref=pick("git_ref", extracted.git_ref, git_ref.strip()),
        version=pick("version", extracted.version, version.strip()),
    )
    if merged.document_key and (not merged.model or not merged.region or not merged.lang):
        parts = merged.document_key.split("_")
        if len(parts) >= 2:
            merged = MessageTargetSelector(
                record_id=merged.record_id,
                document_id=merged.document_id,
                document_key=merged.document_key,
                model=merged.model or parts[0],
                region=merged.region or parts[1].upper(),
                lang=merged.lang or (parts[2].lower() if len(parts) >= 3 else ""),
                build_family=merged.build_family,
                git_ref=merged.git_ref,
                version=merged.version,
            )
    return merged, _unique_preserve_order(warnings)


def build_route(action: str) -> MessageControlRoute | None:
    if action == ACTION_QUERY_STATUS:
        return MessageControlRoute(
            state_surface="review_init + Document_link",
            reply_fields=("Review_status", "PR_url", "构建结果", "Document link", "Document directory"),
        )
    if action == ACTION_START_REVIEW:
        return MessageControlRoute(
            state_surface="review_init",
            workflow_action="Start Review",
            workflow_file=".github/workflows/feishu-start-review.yml",
            reply_fields=("Review_status", "Git_ref", "PR_url"),
        )
    if action == ACTION_BUILD_DRAFT_PACKAGE:
        return MessageControlRoute(
            state_surface="Document_link",
            workflow_action="Build Draft Package",
            workflow_file=".github/workflows/feishu-draft-build-queue.yml",
            reply_fields=("构建结果", "Document link", "Document directory"),
        )
    if action == ACTION_PUBLISH:
        return MessageControlRoute(
            state_surface="Document_link",
            workflow_action="Publish",
            workflow_file=".github/workflows/feishu-build-queue.yml",
            reply_fields=("构建结果", "Document link", "Document directory"),
        )
    return None


def has_stable_selector(selector: MessageTargetSelector) -> bool:
    return bool(
        selector.record_id
        or selector.document_id
        or selector.document_key
        or selector.git_ref
        or (selector.model and selector.build_family)
    )


def resolve_required_fields(
    action: str,
    selector: MessageTargetSelector,
    *,
    known_families: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    missing: list[str] = []
    warnings: list[str] = []
    if not has_stable_selector(selector):
        missing.append("selector")
    if selector.build_family and selector.build_family not in known_families:
        warnings.append(f"unknown_build_family:{selector.build_family}")
    if action in {ACTION_START_REVIEW, ACTION_BUILD_DRAFT_PACKAGE, ACTION_PUBLISH}:
        if not selector.build_family or selector.build_family not in known_families:
            missing.append("build_family")
    if action in {ACTION_BUILD_DRAFT_PACKAGE, ACTION_PUBLISH} and not selector.git_ref:
        missing.append("git_ref")
    return _unique_preserve_order(missing), _unique_preserve_order(warnings)


def resolve_message_control(
    *,
    raw_message: str,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    record_id: str = "",
    document_id: str = "",
    document_key: str = "",
    model: str = "",
    region: str = "",
    lang: str = "",
    build_family: str = "",
    git_ref: str = "",
    version: str = "",
    confirmed: bool = False,
) -> MessageControlResolution:
    family_config_map = collect_family_config_map(repo_root=repo_root, config_loader=config_loader)
    known_families = tuple(sorted(family_config_map))
    normalized_message = normalize_message_text(raw_message)
    action = detect_action(normalized_message)
    extracted_selector = extract_selector_from_message(normalized_message, known_families)
    selector, override_warnings = merge_selector(
        extracted_selector,
        record_id=record_id,
        document_id=document_id,
        document_key=document_key,
        model=model,
        region=region,
        lang=lang,
        build_family=build_family,
        git_ref=git_ref,
        version=version,
    )

    if not action:
        return MessageControlResolution(
            phase="phase0",
            raw_message=raw_message,
            normalized_message=normalized_message,
            status=STATUS_UNRESOLVED,
            selector=selector,
            warnings=override_warnings,
            known_build_families=known_families,
        )

    missing_fields, route_warnings = resolve_required_fields(action, selector, known_families=known_families)
    warnings = _unique_preserve_order(list(override_warnings) + list(route_warnings))
    confirmation_required = action == ACTION_PUBLISH
    if missing_fields:
        status = STATUS_NEEDS_INPUT
    elif confirmation_required and not confirmed:
        status = STATUS_NEEDS_CONFIRMATION
    else:
        status = STATUS_READY

    resolved_config_path = ""
    if selector.build_family in family_config_map and len(family_config_map[selector.build_family]) == 1:
        config_path = family_config_map[selector.build_family][0]
        try:
            resolved_config_path = str(config_path.relative_to(repo_root))
        except ValueError:
            resolved_config_path = str(config_path)

    return MessageControlResolution(
        phase="phase0",
        raw_message=raw_message,
        normalized_message=normalized_message,
        action=action,
        status=status,
        selector=selector,
        missing_fields=missing_fields,
        warnings=warnings,
        confirmation_required=confirmation_required,
        confirmed=confirmed and confirmation_required,
        route=build_route(action),
        resolved_config_path=resolved_config_path,
        known_build_families=known_families,
    )
