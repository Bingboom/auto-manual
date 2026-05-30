from __future__ import annotations

US_SINGLE_LANGUAGE_TARGET_CONFIGS: dict[str, str] = {
    "en": "configs/config.us-en.yaml",
    "es": "configs/config.us-es.yaml",
    "fr": "configs/config.us-fr.yaml",
}

LANGUAGE_BATCH_TARGET_CONFIGS: dict[str, str] = {
    **US_SINGLE_LANGUAGE_TARGET_CONFIGS,
    "ja": "configs/config.ja.yaml",
}

REVIEW_WORKSPACE_TARGET_CONFIGS: tuple[str, ...] = (
    *LANGUAGE_BATCH_TARGET_CONFIGS.values(),
    "configs/config.zh.yaml",
)

FAMILY_DEFAULT_CONFIGS: dict[str, str] = {
    "US": "configs/config.us.yaml",
    "EU": "configs/config.eu.yaml",
    "JP": "configs/config.ja.yaml",
    "CN": "configs/config.zh.yaml",
}
