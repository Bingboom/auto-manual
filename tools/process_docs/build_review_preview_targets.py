from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from tools.build_docs import load_config
from tools.review_support import review_content_exists
from tools.script_bootstrap import bootstrap_repo_root
from tools.utils.path_utils import Paths
from tools.target_defaults import (
    FAMILY_DEFAULT_CONFIGS,
    REVIEW_WORKSPACE_TARGET_CONFIGS,
)


ROOT = bootstrap_repo_root(__file__, parent_count=2)
_PATHS = Paths(root=ROOT)
FAMILY_ORDER = ("US", "JP", "CN")


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


WORKSPACE_TARGET_CONFIGS: tuple[str, ...] = REVIEW_WORKSPACE_TARGET_CONFIGS
ReviewAvailability = set[tuple[str, str, str | None]]


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def path_for_display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _load_workspace_target_template(config_name: str) -> WorkspaceTargetTemplate:
    config_path = (ROOT / config_name).resolve()
    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    family = str(build_cfg.get("default_region") or "").strip().upper()
    if not family:
        raise RuntimeError(f"Review preview target config is missing build.default_region: {config_name}")
    raw_languages = build_cfg.get("languages")
    if not isinstance(raw_languages, list) or len(raw_languages) != 1:
        raise RuntimeError(
            f"Review preview target config must declare exactly one build language: {config_name}"
        )
    return WorkspaceTargetTemplate(
        family=family,
        language=str(raw_languages[0]).strip().lower(),
        config=config_name,
        include_lang_in_output_path=bool(build_cfg.get("include_lang_in_output_path", False)),
    )


def _load_workspace_target_templates() -> tuple[WorkspaceTargetTemplate, ...]:
    return tuple(_load_workspace_target_template(config_name) for config_name in WORKSPACE_TARGET_CONFIGS)


@lru_cache(maxsize=1)
def workspace_target_templates() -> tuple[WorkspaceTargetTemplate, ...]:
    return _load_workspace_target_templates()


class _WorkspaceTargetTemplatesProxy(Sequence[WorkspaceTargetTemplate]):
    """Preserve the public iterable surface without loading config at import time."""

    def _resolved(self) -> tuple[WorkspaceTargetTemplate, ...]:
        return workspace_target_templates()

    def __iter__(self) -> Iterator[WorkspaceTargetTemplate]:
        return iter(self._resolved())

    def __len__(self) -> int:
        return len(self._resolved())

    def __getitem__(self, index: int) -> WorkspaceTargetTemplate:
        return self._resolved()[index]

    def __repr__(self) -> str:
        return repr(self._resolved())


WORKSPACE_TARGET_TEMPLATES: Sequence[WorkspaceTargetTemplate] = _WorkspaceTargetTemplatesProxy()


def default_family_config_for_region(region: str) -> str:
    config_name = FAMILY_DEFAULT_CONFIGS.get((region or "").strip().upper())
    if config_name is None:
        raise RuntimeError(
            "Review preview requires --config when --region is outside the supported family defaults (US, JP, CN)."
        )
    return config_name


def resolved_primary_config_path(args: argparse.Namespace) -> Path:
    raw_config = getattr(args, "config", None)
    if isinstance(raw_config, str) and raw_config.strip():
        return resolve_path(raw_config)
    return resolve_path(default_family_config_for_region(str(getattr(args, "region", ""))))


def output_root_for_target(model: str, target: WorkspaceTarget) -> Path:
    root = _PATHS.docs_build_dir / model / target.family
    if target.include_lang_in_output_path:
        root = root / target.language
    return root


def html_root_for_target(model: str, target: WorkspaceTarget) -> Path:
    return output_root_for_target(model, target) / "html"


def word_root_for_target(model: str, target: WorkspaceTarget) -> Path:
    return output_root_for_target(model, target) / "word"


def tracked_root_for_target(args: argparse.Namespace, target: WorkspaceTarget) -> Path:
    if args.tracked_root and target.family == args.region and target.model == args.model:
        return resolve_path(args.tracked_root)
    return (_PATHS.review_dir / target.model / target.family).resolve()


def diff_config_for_family(args: argparse.Namespace, family: str) -> Path:
    if family == args.region:
        return resolved_primary_config_path(args)
    return resolve_path(default_family_config_for_region(family))


def target_templates_for_family(family: str) -> list[WorkspaceTargetTemplate]:
    return [template for template in workspace_target_templates() if template.family == family]


def build_workspace_target(model: str, template: WorkspaceTargetTemplate) -> WorkspaceTarget:
    return WorkspaceTarget(
        model=model,
        family=template.family,
        language=template.language,
        config=template.config,
        include_lang_in_output_path=template.include_lang_in_output_path,
    )


def target_sort_key(target: WorkspaceTarget) -> tuple[int, str, str]:
    family_rank = FAMILY_ORDER.index(target.family) if target.family in FAMILY_ORDER else len(FAMILY_ORDER)
    return (family_rank, target.model, target.language)


def review_models() -> list[str]:
    review_root = _PATHS.review_dir
    if not review_root.exists():
        return []
    return sorted(path.name for path in review_root.iterdir() if path.is_dir())


def config_template_for_path(config_path: Path) -> WorkspaceTargetTemplate | None:
    resolved = config_path.resolve()
    for template in workspace_target_templates():
        if resolve_path(template.config) == resolved:
            return template
    return None


def requested_workspace_target(args: argparse.Namespace) -> WorkspaceTarget:
    config_path = resolved_primary_config_path(args)
    matched_template = config_template_for_path(config_path)
    if matched_template is not None:
        return build_workspace_target(args.model, matched_template)

    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    languages = build_cfg.get("languages", [])
    if not isinstance(languages, list) or not languages:
        raise RuntimeError(f"Review preview could not infer a workspace language from config: {config_path}")
    language = str(languages[0]).strip().lower()
    include_lang = bool(build_cfg.get("include_lang_in_output_path", False))
    return WorkspaceTarget(
        model=args.model,
        family=args.region,
        language=language,
        config=path_for_display(config_path),
        include_lang_in_output_path=include_lang,
    )


def workspace_families_for_request(args: argparse.Namespace) -> tuple[str, ...]:
    preferred_family = (args.region or "").strip().upper()
    if preferred_family == "CN":
        return ("CN",)
    return FAMILY_ORDER


def _review_availability_keys_for_target(target: WorkspaceTarget) -> tuple[tuple[str, str, str | None], ...]:
    keys: list[tuple[str, str, str | None]] = [(target.model, target.family, target.language)]
    if (target.language or "").strip():
        keys.append((target.model, target.family, None))
    return tuple(keys)


def collect_review_availability(*, docs_dir: Path, targets: list[WorkspaceTarget]) -> ReviewAvailability:
    availability: ReviewAvailability = set()
    candidates: set[tuple[str, str, str | None]] = set()
    for target in targets:
        candidates.update(_review_availability_keys_for_target(target))
    for model, family, lang in sorted(candidates, key=lambda item: (item[0], item[1], item[2] or "")):
        if review_content_exists(
            docs_dir=docs_dir,
            model=model,
            region=family,
            lang=lang,
        ):
            availability.add((model, family, lang))
    return availability


def target_has_review_bundle(
    target: WorkspaceTarget,
    *,
    review_availability: ReviewAvailability | None = None,
    docs_dir: Path | None = None,
) -> bool:
    if review_availability is None:
        actual_docs_dir = docs_dir or _PATHS.docs_dir
        review_availability = collect_review_availability(docs_dir=actual_docs_dir, targets=[target])
    return any(key in review_availability for key in _review_availability_keys_for_target(target))


def collect_workspace_target_candidates(
    args: argparse.Namespace,
    *,
    requested_target: WorkspaceTarget | None = None,
) -> list[WorkspaceTarget]:
    actual_requested_target = requested_target or requested_workspace_target(args)
    targets_by_key: dict[tuple[str, str, str], WorkspaceTarget] = {actual_requested_target.key: actual_requested_target}

    if args.all_review_models:
        for model in review_models():
            for template in workspace_target_templates():
                target = build_workspace_target(model, template)
                targets_by_key[target.key] = target
    else:
        for family in workspace_families_for_request(args):
            for template in target_templates_for_family(family):
                target = build_workspace_target(args.model, template)
                targets_by_key[target.key] = target

    return sorted(targets_by_key.values(), key=target_sort_key)


def build_spec_for_target(
    args: argparse.Namespace,
    target: WorkspaceTarget,
    *,
    requested_target: WorkspaceTarget,
    review_availability: ReviewAvailability | None = None,
    docs_dir: Path | None = None,
) -> dict[str, object]:
    config_path = resolve_path(target.config)
    output_root = output_root_for_target(target.model, target)
    has_review_bundle = target_has_review_bundle(
        target,
        review_availability=review_availability,
        docs_dir=docs_dir,
    )
    source_mode = "review" if has_review_bundle else "runtime"
    source_label = source_mode
    if target.key == requested_target.key:
        requested_source = args.source
        if requested_source == "review" and not has_review_bundle:
            source_mode = "runtime"
            source_label = "runtime"
        else:
            source_mode = requested_source
            source_label = requested_source

    return {
        "config_path": config_path,
        "source_mode": source_mode,
        "source_label": source_label,
        "output_root": output_root,
    }


def build_export_command(
    *,
    action: str,
    model: str,
    config_path: Path,
    family: str,
    source_mode: str,
    no_clean: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(ROOT / "build.py"),
        action,
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        family,
        "--source",
        source_mode,
    ]
    if no_clean:
        cmd.append("--no-clean")
    return cmd


def build_diff_command(*, args: argparse.Namespace, target: WorkspaceTarget, tracked_root: Path) -> list[str]:
    return [
        sys.executable,
        str(ROOT / "build.py"),
        "diff-report",
        "--config",
        str(diff_config_for_family(args, target.family)),
        "--model",
        target.model,
        "--region",
        target.family,
        "--tracked-root",
        str(tracked_root),
        "--from-ref",
        args.from_ref,
        "--to-ref",
        args.to_ref,
    ]


def discover_workspace_targets(
    args: argparse.Namespace,
    *,
    requested_target: WorkspaceTarget | None = None,
    review_availability: ReviewAvailability | None = None,
    docs_dir: Path | None = None,
) -> list[WorkspaceTarget]:
    actual_requested_target = requested_target or requested_workspace_target(args)
    target_candidates = collect_workspace_target_candidates(args, requested_target=actual_requested_target)
    actual_docs_dir = docs_dir or _PATHS.docs_dir
    actual_review_availability = review_availability
    if actual_review_availability is None:
        actual_review_availability = collect_review_availability(
            docs_dir=actual_docs_dir,
            targets=target_candidates,
        )

    selected: list[WorkspaceTarget] = []
    for target in target_candidates:
        if target.key != actual_requested_target.key and args.source == "review":
            if not target_has_review_bundle(target, review_availability=actual_review_availability):
                continue
        selected.append(target)
    return selected
