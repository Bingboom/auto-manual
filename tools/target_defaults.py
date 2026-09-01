from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.config_loader import load_config_mapping
from tools.utils.path_utils import Paths, repo_root


_ROOT = repo_root()
_CONFIGS_DIR = Paths(root=_ROOT).configs_dir
_FAMILY_ORDER = ("US", "EU", "JP", "CN", "KR")


@dataclass(frozen=True)
class TargetDefaults:
    """Config-derived compatibility surfaces used by existing callers."""

    us_single_language_target_configs: dict[str, str]
    language_batch_target_configs: dict[str, str]
    review_workspace_target_configs: tuple[str, ...]
    family_default_configs: dict[str, str]


@dataclass(frozen=True)
class _ConfigMetadata:
    path: Path
    family: str
    languages: tuple[str, ...]
    include_lang_in_output_path: bool
    queue_by_document_key: bool
    family_default: bool


def _config_reference(path: Path) -> str:
    """Return the repo-relative config path expected by CLI callers."""

    try:
        return path.resolve().relative_to(_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_config_metadata(config_path: Path) -> _ConfigMetadata:
    config = load_config_mapping(config_path)
    build_raw = config.get("build", {})
    build = build_raw if isinstance(build_raw, dict) else {}

    raw_languages = build.get("languages", [])
    languages = (
        tuple(str(language).strip().lower() for language in raw_languages if str(language).strip())
        if isinstance(raw_languages, list)
        else ()
    )
    return _ConfigMetadata(
        path=config_path,
        family=str(build.get("default_region") or "").strip().upper(),
        languages=languages,
        include_lang_in_output_path=bool(build.get("include_lang_in_output_path", False)),
        queue_by_document_key=bool(build.get("queue_by_document_key", False)),
        family_default=build.get("family_default") is True,
    )


def _scan_configs(configs_dir: Path) -> tuple[_ConfigMetadata, ...]:
    paths = sorted(configs_dir.glob("config*.yaml"))
    if not paths:
        raise RuntimeError(f"No config*.yaml files found under {configs_dir}")
    return tuple(_read_config_metadata(path) for path in paths)


def _language_config_map(
    configs: tuple[_ConfigMetadata, ...],
    *,
    family: str,
    include_lang_in_output_path: bool | None,
) -> dict[str, str]:
    selected = [
        config
        for config in configs
        if config.family == family
        and len(config.languages) == 1
        and (
            include_lang_in_output_path is None
            or config.include_lang_in_output_path is include_lang_in_output_path
        )
    ]
    by_language: dict[str, list[_ConfigMetadata]] = {}
    for config in selected:
        by_language.setdefault(config.languages[0], []).append(config)

    result: dict[str, str] = {}
    for language, candidates in sorted(by_language.items()):
        if len(candidates) == 1:
            result[language] = _config_reference(candidates[0].path)
            continue
        explicit = [config for config in candidates if config.family_default]
        if len(explicit) != 1:
            names = ", ".join(_config_reference(config.path) for config in candidates)
            raise RuntimeError(
                f"Multiple language configs for {family}/{language} without exactly one "
                f"explicit family_default: {names}"
            )
        result[language] = _config_reference(explicit[0].path)
    return result


def _family_config_score(config: _ConfigMetadata) -> int:
    """Prefer merged family configs over language-specific variants."""

    score = 0
    if not config.include_lang_in_output_path:
        score += 100
    if config.queue_by_document_key:
        score += 20
    if len(config.languages) == 1:
        score += 10
    if config.path.stem == f"config.{config.family.lower()}":
        score += 1
    return score


def _family_default_map(
    configs: tuple[_ConfigMetadata, ...],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for family in _FAMILY_ORDER:
        candidates = [config for config in configs if config.family == family]
        if not candidates:
            raise RuntimeError(f"No default config found for family {family!r}")
        explicit = [config for config in candidates if config.family_default]
        if explicit:
            if len(explicit) > 1:
                names = ", ".join(_config_reference(config.path) for config in explicit)
                raise RuntimeError(
                    f"Multiple explicit family_default configs for family {family!r}: {names}"
                )
            result[family] = _config_reference(explicit[0].path)
            continue
        candidates.sort(key=lambda config: (-_family_config_score(config), config.path.name))
        best_score = _family_config_score(candidates[0])
        best = [config for config in candidates if _family_config_score(config) == best_score]
        if len(best) > 1:
            names = ", ".join(_config_reference(config.path) for config in best)
            raise RuntimeError(f"Default config resolution is ambiguous for family {family!r}: {names}")
        result[family] = _config_reference(best[0].path)
    return result


def discover_target_defaults(configs_dir: Path = _CONFIGS_DIR) -> TargetDefaults:
    """Derive legacy target-default maps from the repository config scan."""

    configs = _scan_configs(configs_dir)
    family_defaults = _family_default_map(configs)
    us_single = _language_config_map(configs, family="US", include_lang_in_output_path=True)
    jp_single = _language_config_map(configs, family="JP", include_lang_in_output_path=None)
    language_batch = {**us_single, **jp_single}
    review_workspace = (*language_batch.values(), family_defaults["CN"])
    return TargetDefaults(
        us_single_language_target_configs=us_single,
        language_batch_target_configs=language_batch,
        review_workspace_target_configs=review_workspace,
        family_default_configs=family_defaults,
    )


_DEFAULTS = discover_target_defaults()

US_SINGLE_LANGUAGE_TARGET_CONFIGS: dict[str, str] = _DEFAULTS.us_single_language_target_configs

LANGUAGE_BATCH_TARGET_CONFIGS: dict[str, str] = _DEFAULTS.language_batch_target_configs

REVIEW_WORKSPACE_TARGET_CONFIGS: tuple[str, ...] = _DEFAULTS.review_workspace_target_configs

FAMILY_DEFAULT_CONFIGS: dict[str, str] = _DEFAULTS.family_default_configs
