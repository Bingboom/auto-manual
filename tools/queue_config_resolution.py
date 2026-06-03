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
    return text


def build_languages(cfg: dict[str, Any]) -> list[str]:
    langs = build_cfg(cfg).get("languages", ["en"])
    return [normalize_language(item) for item in langs if str(item).strip()] or ["en"]


def queue_by_document_key(cfg: dict[str, Any]) -> bool:
    return bool(build_cfg(cfg).get("queue_by_document_key"))


def config_family_id(cfg: dict[str, Any]) -> str:
    return normalize_build_family(build_cfg(cfg).get("family_id"))


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
    normalized_region = normalize_region(region)
    languages = build_languages(cfg)
    normalized_lang = normalize_language(lang, supported=languages)
    normalized_action = normalize_queue_workflow_action(workflow_action)
    current_build_cfg = build_cfg(cfg)
    include_lang_in_output_path = bool(current_build_cfg.get("include_lang_in_output_path"))
    if family_id != build_family:
        raise RuntimeError(
            f"Config {config_path.name} does not match Build_family={build_family!r}; family_id={family_id!r}"
        )

    default_region = config_default_region(cfg)
    if default_region and default_region != normalized_region:
        raise RuntimeError(
            f"Build_family {build_family!r} routes to region {default_region!r}, not {normalized_region!r}"
        )

    primary_lang = languages[0] if languages else ""
    if normalized_action == "publish":
        if normalized_lang:
            raise RuntimeError("Publish queue rows must leave Lang blank")
        if include_lang_in_output_path:
            raise RuntimeError(
                "Publish queue rows must use a whole-book Build_family, not a single-language family"
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


def config_match_score(*, config_path: Path, cfg: dict[str, Any], region: str, lang: str | None) -> int | None:
    current_build_cfg = build_cfg(cfg)
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


def review_start_region_match_score(*, config_path: Path, cfg: dict[str, Any], region: str) -> int | None:
    current_build_cfg = build_cfg(cfg)
    default_region = normalize_region(current_build_cfg.get("default_region"))
    if default_region != normalize_region(region):
        return None
    languages = build_languages(cfg)
    score = 0
    if queue_by_document_key(cfg):
        score += 100
    if len(languages) == 1:
        score += 10
    if not bool(current_build_cfg.get("include_lang_in_output_path")):
        score += 5
    if region.lower() in config_path.name.lower():
        score += 1
    return score


def resolve_review_start_config_path_for_target(
    *,
    repo_root: Path,
    region: str,
    lang: str | None,
    build_family: str | None = None,
    config_loader: Callable[[Path], dict[str, Any]],
) -> Path:
    try:
        return resolve_config_path_for_task(
            repo_root=repo_root,
            region=region,
            lang=lang,
            build_family=build_family,
            config_loader=config_loader,
        )
    except RuntimeError as exc:
        if str(lang or "").strip() or str(build_family or "").strip():
            raise

        candidates: list[tuple[int, Path]] = []
        for config_path in sorted((repo_root / PathSegments.CONFIGS).glob("config*.yaml")):
            try:
                cfg = config_loader(config_path)
            except RuntimeError:
                continue
            score = review_start_region_match_score(config_path=config_path, cfg=cfg, region=region)
            if score is None:
                continue
            candidates.append((score, config_path))

        if not candidates:
            raise exc
        candidates.sort(key=lambda item: (-item[0], item[1].name))
        best_score = candidates[0][0]
        best_paths = [path for score, path in candidates if score == best_score]
        if len(best_paths) > 1:
            names = ", ".join(path.name for path in best_paths)
            raise RuntimeError(
                f"Review-start config resolution is ambiguous for region={normalize_region(region)!r}: {names}"
            ) from exc
        return candidates[0][1]


def resolve_config_path_for_task(
    *,
    repo_root: Path,
    region: str,
    lang: str | None,
    build_family: str | None = None,
    workflow_action: str | None = None,
    config_loader: Callable[[Path], dict[str, Any]],
) -> Path:
    normalized_build_family = normalize_build_family(build_family)
    if normalized_build_family:
        family_candidates: list[tuple[Path, dict[str, Any]]] = []
        for config_path in sorted((repo_root / PathSegments.CONFIGS).glob("config*.yaml")):
            try:
                cfg = config_loader(config_path)
            except RuntimeError:
                continue
            if config_family_id(cfg) != normalized_build_family:
                continue
            family_candidates.append((config_path, cfg))

        if not family_candidates:
            raise RuntimeError(f"No config family matches Build_family={normalized_build_family!r}")
        if len(family_candidates) > 1:
            names = ", ".join(path.name for path, _ in family_candidates)
            raise RuntimeError(
                f"Build_family {normalized_build_family!r} matches multiple config files: {names}"
            )
        config_path, cfg = family_candidates[0]
        validate_family_config_request(
            config_path=config_path,
            cfg=cfg,
            build_family=normalized_build_family,
            region=region,
            lang=lang,
            workflow_action=workflow_action,
        )
        return config_path

    candidates: list[tuple[int, Path]] = []
    for config_path in sorted((repo_root / PathSegments.CONFIGS).glob("config*.yaml")):
        try:
            cfg = config_loader(config_path)
        except RuntimeError:
            continue
        score = config_match_score(config_path=config_path, cfg=cfg, region=region, lang=lang)
        if score is None:
            continue
        candidates.append((score, config_path))

    if not candidates:
        raise RuntimeError(f"No config family matches region='{region}' and lang='{lang}'")
    candidates.sort(key=lambda item: (-item[0], item[1].name))
    return candidates[0][1]
