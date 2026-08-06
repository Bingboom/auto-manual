"""Language tokens and aliases used by queue query parsing."""

from __future__ import annotations

import re

from tools import lang_registry


_REGISTRY_LANG_ALIASES = {
    alias.casefold(): code
    for alias, code in lang_registry.LANGUAGE_BY_ALIAS.items()
}

LANG_CODES = frozenset(
    (*_REGISTRY_LANG_ALIASES, "cn", "pt", "pt-br", "zh-tw", "zh_tw", "zh-hant")
)
LANG_ALIASES = {
    **_REGISTRY_LANG_ALIASES,
    "英语": "en",
    "英文": "en",
    "english": "en",
    "法语": "fr",
    "法文": "fr",
    "french": "fr",
    "西语": "es",
    "西班牙语": "es",
    "spanish": "es",
    "德语": "de",
    "德文": "de",
    "german": "de",
    "意语": "it",
    "意大利语": "it",
    "italian": "it",
    "日语": "ja",
    "日文": "ja",
    "japanese": "ja",
    "中文": "zh",
    "汉语": "zh",
    "chinese": "zh",
    "cn": "zh",
    "葡语": "pt",
    "葡萄牙语": "pt",
    "portuguese": "pt-BR",
    "brazilian portuguese": "pt-BR",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "br": "pt-BR",
    "韩语": "ko",
    "韩文": "ko",
    "korean": "ko",
    "乌克兰语": "uk",
    "乌语": "uk",
    "ukrainian": "uk",
    "zh-tw": "zh-TW",
    "zh_tw": "zh-TW",
    "zh-hant": "zh-TW",
}
SUPPORTED_LANGS = frozenset(spec.code for spec in lang_registry.LANGUAGE_REGISTRY)
LANG_NAME_PATTERN = re.compile(
    "|".join(re.escape(name) for name in sorted(LANG_ALIASES, key=len, reverse=True)),
    re.IGNORECASE,
)


# Feishu display names carry a regional qualifier: `英语（美式）`,
# `葡萄牙语（巴西）`. The qualifier names a variant of the same repo language,
# so strip it and retry rather than enumerating every spelling.
_QUALIFIER_RE = re.compile(r"[（(][^）)]*[）)]\s*$")


def canonical_query_lang(value: object) -> str:
    """Normalize a queue-query language token to a registered language code."""
    token = str(value or "").strip().casefold()
    normalized = LANG_ALIASES.get(token, token)
    spec = lang_registry.language_spec(normalized)
    if spec is not None:
        return spec.code
    if normalized in {"pt", "br", "pt-br", "pt_br"}:
        return "pt-BR"
    if normalized == token:
        base = _QUALIFIER_RE.sub("", token).strip()
        if base and base != token:
            return canonical_query_lang(base)
    return normalized
