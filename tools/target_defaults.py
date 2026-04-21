from __future__ import annotations

US_SINGLE_LANGUAGE_TARGET_CONFIGS: dict[str, str] = {
    "en": "config.us-en.yaml",
    "es": "config.us-es.yaml",
    "fr": "config.us-fr.yaml",
}

LANGUAGE_BATCH_TARGET_CONFIGS: dict[str, str] = {
    **US_SINGLE_LANGUAGE_TARGET_CONFIGS,
    "ja": "config.ja.yaml",
}

REVIEW_WORKSPACE_TARGET_CONFIGS: tuple[str, ...] = (
    *LANGUAGE_BATCH_TARGET_CONFIGS.values(),
    "config.zh.yaml",
)

FAMILY_DEFAULT_CONFIGS: dict[str, str] = {
    "US": "config.us.yaml",
    "EU": "config.eu.yaml",
    "JP": "config.ja.yaml",
    "CN": "config.zh.yaml",
}
