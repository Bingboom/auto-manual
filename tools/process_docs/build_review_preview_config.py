from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.build_docs import load_config
from tools.queue_config_resolution import resolve_declared_target_config_path
from tools.script_bootstrap import bootstrap_repo_root
from tools.utils.path_utils import Paths


ROOT = bootstrap_repo_root(__file__, parent_count=2)
_PATHS = Paths(root=ROOT)


@dataclass(frozen=True)
class WorkspaceTarget:
    model: str
    family: str
    language: str
    config: str
    include_lang_in_output_path: bool

    @property
    def label(self) -> str:
        return f"{self.model}/{self.family}/{self.language}"

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.model, self.family, self.language)


@dataclass(frozen=True)
class WorkspaceTargetTemplate:
    family: str
    language: str
    config: str
    include_lang_in_output_path: bool


def _path_for_display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def resolve_preview_target_config_path(
    *,
    model: str,
    family: str,
    language: str | None,
) -> Path | None:
    resolved = resolve_declared_target_config_path(
        config_paths=sorted(_PATHS.configs_dir.glob("config*.yaml")),
        model=model,
        region=family,
        lang=language,
        config_loader=load_config,
    )
    return resolved.resolve() if resolved is not None else None


def _workspace_target_from_config(
    *,
    model: str,
    config_path: Path,
    language: str | None,
) -> WorkspaceTarget:
    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    family = str(build_cfg.get("default_region") or "").strip().upper()
    raw_languages = build_cfg.get("languages", [])
    languages = (
        [str(item).strip().lower() for item in raw_languages if str(item).strip()]
        if isinstance(raw_languages, list)
        else []
    )
    if not family or not languages:
        raise RuntimeError(f"Review preview target config is incomplete: {_path_for_display(config_path)}")
    normalized_language = str(language or "").strip().lower()
    selected_language = normalized_language if normalized_language in languages else languages[0]
    return WorkspaceTarget(
        model=model,
        family=family,
        language=selected_language,
        config=_path_for_display(config_path),
        include_lang_in_output_path=bool(build_cfg.get("include_lang_in_output_path", False)),
    )


def registered_workspace_targets_for_model(
    model: str,
    templates: Sequence[WorkspaceTargetTemplate],
) -> list[WorkspaceTarget]:
    targets: list[WorkspaceTarget] = []
    seen_output_configs: set[tuple[str, str, str]] = set()
    for template in templates:
        config_path = resolve_preview_target_config_path(
            model=model,
            family=template.family,
            language=template.language,
        )
        if config_path is None:
            continue
        target = _workspace_target_from_config(
            model=model,
            config_path=config_path,
            language=template.language,
        )
        identity = (
            target.model,
            target.family,
            target.config if not target.include_lang_in_output_path else target.language,
        )
        if identity in seen_output_configs:
            continue
        seen_output_configs.add(identity)
        targets.append(target)
    return targets
