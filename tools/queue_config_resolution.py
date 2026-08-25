from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.language_aliases import language_key, normalize_language, normalize_region
from tools.utils.path_utils import PathSegments


def build_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    build_cfg_raw = cfg.get("build", {})
    return build_cfg_raw if isinstance(build_cfg_raw, dict) else {}


def normalize_build_family(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_queue_workflow_action(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"build draft package", "draft"}:
        return "draft"
    if text == "publish":
        return "publish"
    if text in {"web publish", "web_publish", "web-publish"}:
        return "web_publish"
    return text


def build_languages(cfg: dict[str, Any]) -> list[str]:
    langs = build_cfg(cfg).get("languages", ["en"])
    return [normalize_language(item) for item in langs if str(item).strip()] or ["en"]


def queue_by_document_key(cfg: dict[str, Any]) -> bool:
    return bool(build_cfg(cfg).get("queue_by_document_key"))


def config_family_id(cfg: dict[str, Any]) -> str:
    return normalize_build_family(build_cfg(cfg).get("family_id"))


def config_language_family(cfg: dict[str, Any]) -> str:
    """Return the queue row's language-range family for this config.

    Most existing configs use the same value for their internal config identity
    and queue language family. Target-specific skeleton configs may keep a
    unique ``family_id`` while sharing a row language family with the generic
    regional config.
    """

    current_build_cfg = build_cfg(cfg)
    return normalize_build_family(
        current_build_cfg.get("language_family") or current_build_cfg.get("family_id")
    )


def config_requires_target_match(cfg: dict[str, Any]) -> bool:
    current_build_cfg = build_cfg(cfg)
    return bool(
        current_build_cfg.get("queue_requires_target_match")
        or current_build_cfg.get("queue_requires_build_family")
    )


def config_accepts_build_family(cfg: dict[str, Any], build_family: str) -> bool:
    normalized = normalize_build_family(build_family)
    return normalized in {config_language_family(cfg), config_family_id(cfg)}


def config_default_region(cfg: dict[str, Any]) -> str:
    return normalize_region(build_cfg(cfg).get("default_region"))


def validate_family_config_request(
    *,
    config_path: Path,
    cfg: dict[str, Any],
    build_family: str,
    region: str,
    lang: str | None,
    workflow_action: str | None = None,
) -> None:
    family_id = config_family_id(cfg)
    language_family = config_language_family(cfg)
    normalized_region = normalize_region(region)
    languages = build_languages(cfg)
    normalized_lang = normalize_language(lang, supported=languages)
    normalized_action = normalize_queue_workflow_action(workflow_action)
    current_build_cfg = build_cfg(cfg)
    include_lang_in_output_path = bool(current_build_cfg.get("include_lang_in_output_path"))
    if not config_accepts_build_family(cfg, build_family):
        raise RuntimeError(
            f"Config {config_path.name} does not match Build_family={build_family!r}; "
            f"language_family={language_family!r}, family_id={family_id!r}"
        )

    default_region = config_default_region(cfg)
    if default_region and default_region != normalized_region:
        raise RuntimeError(
            f"Build_family {build_family!r} routes to region {default_region!r}, not {normalized_region!r}"
        )

    primary_lang = languages[0] if languages else ""
    if normalized_action in {"publish", "web_publish"}:
        if normalized_lang:
            raise RuntimeError(
                f"{normalized_action.replace('_', ' ').title()} queue rows must leave Lang blank"
            )
        if include_lang_in_output_path:
            raise RuntimeError(
                f"{normalized_action.replace('_', ' ').title()} queue rows must use a whole-book "
                "Build_family, not a single-language family"
            )
    if normalized_action == "draft" and normalized_lang:
        if not queue_by_document_key(cfg) and (len(languages) != 1 or language_key(primary_lang) != language_key(normalized_lang)):
            raise RuntimeError(
                "Build Draft Package rows with Lang must use a single-language Build_family"
            )
    if not normalized_lang:
        return
    if queue_by_document_key(cfg):
        if language_key(normalized_lang) not in {language_key(item) for item in languages}:
            raise RuntimeError(
                f"Build_family {build_family!r} does not include Lang={normalized_lang!r}; supported={languages}"
            )
        return
    if language_key(primary_lang) != language_key(normalized_lang):
        raise RuntimeError(
            f"Build_family {build_family!r} conflicts with Lang={normalized_lang!r}; expected {primary_lang!r}"
        )


def _config_match_score(
    *,
    config_path: Path,
    cfg: dict[str, Any],
    region: str,
    lang: str | None,
    allow_target_specific: bool,
) -> int | None:
    current_build_cfg = build_cfg(cfg)
    # Target-specific skeleton configs never compete for a model-less fallback.
    # They may participate only after an exact model/region target match. This
    # prevents e.g. a battery-pack config from outscoring the generic US host
    # config while still allowing both to share language_family=us-merged.
    if config_requires_target_match(cfg) and not allow_target_specific:
        return None
    default_region = normalize_region(current_build_cfg.get("default_region"))
    languages = build_languages(cfg)
    primary_lang = languages[0] if languages else ""
    normalized_lang = normalize_language(lang, supported=languages)
    if default_region != normalize_region(region):
        return None
    if queue_by_document_key(cfg):
        if normalized_lang:
            if language_key(normalized_lang) not in {language_key(item) for item in languages}:
                return None
            score = 50
        else:
            score = 100
    else:
        if not normalized_lang or language_key(primary_lang) != language_key(normalized_lang):
            return None
        score = 100

    file_name = config_path.name.lower()
    if region.lower() in file_name:
        score += 4
    if language_key(normalized_lang) and language_key(normalized_lang) in file_name:
        score += 4
    if bool(current_build_cfg.get("include_lang_in_output_path")):
        score += 2
    if file_name != "config.us.yaml":
        score += 1
    return score


def config_match_score(*, config_path: Path, cfg: dict[str, Any], region: str, lang: str | None) -> int | None:
    return _config_match_score(
        config_path=config_path,
        cfg=cfg,
        region=region,
        lang=lang,
        allow_target_specific=False,
    )


def config_declares_target(*, cfg: dict[str, Any], model: str, region: str) -> bool:
    current_build_cfg = build_cfg(cfg)
    normalized_model = str(model or "").strip().casefold()
    normalized_region = normalize_region(region)
    targets = current_build_cfg.get("targets", [])
    if isinstance(targets, list) and targets:
        for target in targets:
            if not isinstance(target, dict):
                continue
            target_model = str(target.get("model") or "").strip().casefold()
            target_region = normalize_region(target.get("region"))
            if target_model == normalized_model and target_region == normalized_region:
                return True
        return False
    default_model = str(current_build_cfg.get("default_model") or "").strip().casefold()
    default_region = normalize_region(current_build_cfg.get("default_region"))
    return bool(normalized_model) and default_model == normalized_model and default_region == normalized_region


def target_config_match_score(
    *,
    config_path: Path,
    cfg: dict[str, Any],
    model: str,
    region: str,
    lang: str | None,
) -> int | None:
    """Score a config only after its declared model/region target matches.

    Every queue and preview entrypoint owns a concrete ``Document_Key`` target,
    so a target-specific skeleton can safely participate after this match.
    """
    if not config_declares_target(cfg=cfg, model=model, region=region):
        return None
    if not str(lang or "").strip():
        current_build_cfg = build_cfg(cfg)
        languages = build_languages(cfg)
        score = 0
        if queue_by_document_key(cfg):
            score += 100
        if len(languages) == 1:
            score += 10
        if not bool(current_build_cfg.get("include_lang_in_output_path")):
            score += 5
        if normalize_region(region).lower() in config_path.name.lower():
            score += 1
        return score
    return _config_match_score(
        config_path=config_path,
        cfg=cfg,
        region=region,
        lang=lang,
        allow_target_specific=True,
    )


# Compatibility import for callers and tests introduced with Start Review
# target inference. New code should use the entrypoint-neutral name above.
review_start_config_match_score = target_config_match_score


def _select_scored_target_candidate(
    candidates: list[tuple[int, Path, dict[str, Any]]],
    *,
    model: str,
    region: str,
    lang: str | None,
) -> tuple[Path, dict[str, Any]] | None:
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1].name))
    best_score = candidates[0][0]
    best = [(path, cfg) for score, path, cfg in candidates if score == best_score]
    if len(best) > 1:
        names = ", ".join(path.name for path, _ in best)
        raise RuntimeError(
            "Config resolution is ambiguous for "
            f"model={model!r}, region={region!r}, lang={lang!r}: {names}"
        )
    return best[0]


def _select_declared_target_config(
    loaded_configs: list[tuple[Path, dict[str, Any]]],
    *,
    model: str,
    region: str,
    lang: str | None,
) -> tuple[Path, dict[str, Any]] | None:
    candidates: list[tuple[int, Path, dict[str, Any]]] = []
    for config_path, cfg in loaded_configs:
        score = target_config_match_score(
            config_path=config_path,
            cfg=cfg,
            model=model,
            region=region,
            lang=lang,
        )
        if score is not None:
            candidates.append((score, config_path, cfg))
    return _select_scored_target_candidate(
        candidates,
        model=model,
        region=region,
        lang=lang,
    )


def resolve_declared_target_config_path(
    *,
    config_paths: list[Path],
    model: str,
    region: str,
    lang: str | None,
    config_loader: Callable[[Path], dict[str, Any]],
) -> Path | None:
    loaded_configs: list[tuple[Path, dict[str, Any]]] = []
    for config_path in config_paths:
        try:
            cfg = config_loader(config_path)
        except RuntimeError:
            continue
        loaded_configs.append((config_path, cfg))
    selected = _select_declared_target_config(
        loaded_configs,
        model=model,
        region=region,
        lang=lang,
    )
    return selected[0] if selected is not None else None


def _select_family_candidate(
    candidates: list[tuple[Path, dict[str, Any]]],
    *,
    build_family: str,
) -> tuple[Path, dict[str, Any]]:
    internal_matches = [
        (path, cfg)
        for path, cfg in candidates
        if config_family_id(cfg) == build_family
    ]
    if len(internal_matches) == 1:
        return internal_matches[0]
    if len(candidates) == 1:
        return candidates[0]
    names = ", ".join(path.name for path, _ in candidates)
    raise RuntimeError(
        f"Build_family {build_family!r} matches multiple config files without a unique target: {names}"
    )


def _validate_resolved_config(
    *,
    config_path: Path,
    cfg: dict[str, Any],
    build_family: str | None,
    region: str,
    lang: str | None,
    workflow_action: str | None,
) -> None:
    effective_family = normalize_build_family(build_family) or config_language_family(cfg)
    if not effective_family:
        return
    validate_family_config_request(
        config_path=config_path,
        cfg=cfg,
        build_family=effective_family,
        region=region,
        lang=lang,
        workflow_action=workflow_action,
    )


def resolve_config_path_for_task(
    *,
    repo_root: Path,
    model: str | None = None,
    region: str,
    lang: str | None,
    build_family: str | None = None,
    workflow_action: str | None = None,
    config_loader: Callable[[Path], dict[str, Any]],
) -> Path:
    loaded_configs: list[tuple[Path, dict[str, Any]]] = []
    for config_path in sorted((repo_root / PathSegments.CONFIGS).glob("config*.yaml")):
        try:
            cfg = config_loader(config_path)
        except RuntimeError:
            continue
        loaded_configs.append((config_path, cfg))

    normalized_model = str(model or "").strip()
    normalized_build_family = normalize_build_family(build_family)
    if normalized_build_family:
        family_candidates = [
            (config_path, cfg)
            for config_path, cfg in loaded_configs
            if config_accepts_build_family(cfg, normalized_build_family)
        ]

        if not family_candidates:
            raise RuntimeError(f"No config family matches Build_family={normalized_build_family!r}")

        selected: tuple[Path, dict[str, Any]] | None = None
        if normalized_model:
            selected = _select_declared_target_config(
                family_candidates,
                model=normalized_model,
                region=region,
                lang=lang,
            )

            if selected is None:
                exact_only_targets = [
                    path
                    for path, cfg in loaded_configs
                    if config_requires_target_match(cfg)
                    and config_declares_target(cfg=cfg, model=normalized_model, region=region)
                ]
                if exact_only_targets:
                    names = ", ".join(path.name for path in exact_only_targets)
                    raise RuntimeError(
                        f"Target model={normalized_model!r}, region={region!r} does not support "
                        f"Build_family={normalized_build_family!r}; target configs: {names}"
                    )

        if selected is None:
            generic_candidates = [
                (path, cfg)
                for path, cfg in family_candidates
                if not config_requires_target_match(cfg)
            ]
            # Keep the internal family id as a backwards-compatible explicit
            # selector during the language-family migration (e.g. bp-us).
            fallback_candidates = generic_candidates or family_candidates
            selected = _select_family_candidate(
                fallback_candidates,
                build_family=normalized_build_family,
            )

        config_path, cfg = selected
        _validate_resolved_config(
            config_path=config_path,
            cfg=cfg,
            build_family=normalized_build_family,
            region=region,
            lang=lang,
            workflow_action=workflow_action,
        )
        return config_path

    if normalized_model:
        selected = _select_declared_target_config(
            loaded_configs,
            model=normalized_model,
            region=region,
            lang=lang,
        )
        if selected is not None:
            config_path, cfg = selected
            _validate_resolved_config(
                config_path=config_path,
                cfg=cfg,
                build_family=None,
                region=region,
                lang=lang,
                workflow_action=workflow_action,
            )
            return config_path

    candidates: list[tuple[int, Path]] = []
    for config_path, cfg in loaded_configs:
        score = config_match_score(config_path=config_path, cfg=cfg, region=region, lang=lang)
        if score is not None:
            candidates.append((score, config_path))

    if not candidates:
        raise RuntimeError(f"No config family matches region='{region}' and lang='{lang}'")
    candidates.sort(key=lambda item: (-item[0], item[1].name))
    config_path = candidates[0][1]
    cfg = next(cfg for path, cfg in loaded_configs if path == config_path)
    _validate_resolved_config(
        config_path=config_path,
        cfg=cfg,
        build_family=None,
        region=region,
        lang=lang,
        workflow_action=workflow_action,
    )
    return config_path
