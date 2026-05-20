from __future__ import annotations

from typing import Any, Callable

from tools.language_aliases import language_key, normalize_language


def config_uses_model_token(
    cfg: dict,
    *,
    config_uses_token_in_pages: Callable[[dict, str], bool],
) -> bool:
    return config_uses_token_in_pages(cfg, "model")


def config_uses_region_token(
    cfg: dict,
    *,
    config_uses_token_in_pages: Callable[[dict, str], bool],
) -> bool:
    return config_uses_token_in_pages(cfg, "region")


def resolve_build_model(
    cfg: dict,
    arg_model: str | None,
    *,
    resolve_target_model: Callable[[dict, str | None], str | None],
) -> str | None:
    return resolve_target_model(cfg, arg_model)


def resolve_build_region(
    cfg: dict,
    arg_region: str | None,
    *,
    resolve_target_region: Callable[[dict, str | None], str | None],
) -> str | None:
    return resolve_target_region(cfg, arg_region)


def configured_build_targets(
    cfg: dict,
    *,
    build_target_cls: type[Any],
    resolve_build_model: Callable[[dict, str | None], str | None],
    resolve_build_region: Callable[[dict, str | None], str | None],
    resolve_output_lang: Callable[[dict], str | None],
    arg_lang: str | None = None,
) -> list[Any]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    raw_targets = build_cfg.get("targets")
    if raw_targets is None:
        return []
    if not isinstance(raw_targets, list):
        raise RuntimeError("build.targets must be a list when provided")

    default_model = resolve_build_model(cfg, None)
    default_region = resolve_build_region(cfg, None)
    languages = build_cfg.get("languages", [])
    supported_langs = [str(item).strip() for item in languages if str(item).strip()] if isinstance(languages, list) else []
    output_lang = normalize_language(arg_lang, supported=supported_langs) if (arg_lang or "").strip() else resolve_output_lang(cfg)
    targets: list[Any] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()

    for idx, item in enumerate(raw_targets, start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"build.targets[{idx}] must be a mapping")

        raw_model = item.get("model")
        raw_region = item.get("region")

        model = raw_model.strip() if isinstance(raw_model, str) and raw_model.strip() else default_model
        region = raw_region.strip() if isinstance(raw_region, str) and raw_region.strip() else default_region
        if not model:
            raise RuntimeError(
                f"build.targets[{idx}] could not resolve a model; set targets[{idx}].model or build.default_model"
            )

        key = (model, region, output_lang)
        if key in seen:
            continue
        seen.add(key)
        targets.append(build_target_cls(model=model, region=region, lang=output_lang))

    return targets


def resolve_build_targets(
    cfg: dict,
    *,
    arg_model: str | None,
    arg_region: str | None,
    arg_lang: str | None = None,
    all_targets: bool,
    build_target_cls: type[Any],
    configured_build_targets: Callable[[dict], list[Any]],
    resolve_build_model: Callable[[dict, str | None], str | None],
    resolve_build_region: Callable[[dict, str | None], str | None],
    resolve_output_lang: Callable[[dict], str | None],
) -> list[Any]:
    if all_targets and ((arg_model or "").strip() or (arg_region or "").strip() or (arg_lang or "").strip()):
        raise RuntimeError("Cannot combine --all-targets with --model, --region, or --lang")

    if all_targets:
        targets = configured_build_targets(cfg)
        if targets:
            return targets

    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    raw_languages = build_cfg.get("languages", [])
    supported_langs = [str(item).strip() for item in raw_languages if str(item).strip()] if isinstance(raw_languages, list) else []
    output_lang = normalize_language(arg_lang, supported=supported_langs) if (arg_lang or "").strip() else resolve_output_lang(cfg)
    if output_lang and supported_langs and language_key(output_lang) not in {language_key(item) for item in supported_langs}:
        raise RuntimeError(
            f"Requested --lang {arg_lang!r} is not declared in build.languages: {supported_langs}"
        )

    return [
        build_target_cls(
            model=resolve_build_model(cfg, arg_model),
            region=resolve_build_region(cfg, arg_region),
            lang=output_lang,
        )
    ]
