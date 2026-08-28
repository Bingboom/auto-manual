"""Korean particle (josa) selection for placeholder-backed template text.

Korean picks a particle by whether the preceding syllable ends in a consonant
(받침 / batchim): ``제품은`` but ``배터리는``. A template that writes
``|PRODUCT_NAME|`` cannot know which one it needs, so the ko templates used to
carry both — ``|PRODUCT_NAME|은(는)`` — and the double form printed verbatim,
which Style Guide K11 (``data/terminology_rules.csv``) forbids in a finished
manual.

The fix keeps the choice where the value is known: for every substitution key
this module emits companion keys that carry the value *with* its particle
(``|PRODUCT_NAME_JOSA_EUN|`` -> ``리튬이차전지시스템은``), so a template names the
particle pair it needs and the renderer resolves it once per build.

A value whose reading this module cannot determine (a Latin-script tail that is
not in ``LATIN_FINAL_BATCHIM``) is skipped rather than guessed: the companion key
is simply not emitted, the build fails loudly on the unknown substitution, and a
human decides. Guessing here would print a wrong particle in a shipped manual.
"""

from __future__ import annotations

from collections.abc import Mapping

# Suffix -> (particle after a consonant, particle after a vowel).
JOSA_PAIRS: dict[str, tuple[str, str]] = {
    "EUN": ("은", "는"),
    "EUL": ("을", "를"),
    "I": ("이", "가"),
    "WA": ("과", "와"),
}

_HANGUL_BASE = 0xAC00
_HANGUL_LAST = 0xD7A3
_JONGSEONG_COUNT = 28

# Sino-Korean digit readings: 0 영, 1 일, 3 삼, 6 육, 7 칠, 8 팔 end in a consonant.
_DIGIT_BATCHIM: dict[str, bool] = {
    "0": True,
    "1": True,
    "2": False,
    "3": True,
    "4": False,
    "5": False,
    "6": True,
    "7": True,
    "8": True,
    "9": False,
}

# Latin-script tails whose Korean reading is settled. Keys are lowercase and
# matched against the final whitespace-delimited word of the value.
# ``Jackery`` reads 재키 -> ends in a vowel.
LATIN_FINAL_BATCHIM: dict[str, bool] = {
    "jackery": False,
}

_TRIM_CHARS = " 	 .,:;!?()[]{}'\"“”‘’*"


def _final_token(value: str) -> str:
    stripped = value.strip().strip(_TRIM_CHARS)
    if not stripped:
        return ""
    token = stripped.split()[-1] if " " in stripped else stripped
    return token.strip(_TRIM_CHARS)


def has_batchim(value: str) -> bool | None:
    """Return whether ``value`` ends in a consonant, or ``None`` when unknown."""
    token = _final_token(value)
    if not token:
        return None
    last = token[-1]
    if _HANGUL_BASE <= ord(last) <= _HANGUL_LAST:
        return (ord(last) - _HANGUL_BASE) % _JONGSEONG_COUNT != 0
    if last.isdigit():
        return _DIGIT_BATCHIM[last]
    return LATIN_FINAL_BATCHIM.get(token.lower())


def select_josa(value: str, pair: str) -> str | None:
    """Return the particle for ``value``, or ``None`` when the reading is unknown."""
    if pair not in JOSA_PAIRS:
        raise KeyError(f"Unknown josa pair: {pair!r}")
    batchim = has_batchim(value)
    if batchim is None:
        return None
    after_consonant, after_vowel = JOSA_PAIRS[pair]
    return after_consonant if batchim else after_vowel


def josa_substitutions(substitutions: Mapping[str, str]) -> dict[str, str]:
    """Return ``{KEY}_JOSA_{PAIR}`` substitutions carrying value + particle.

    Keys whose value is empty, or whose reading is unknown, are omitted.
    """
    resolved: dict[str, str] = {}
    for key, raw_value in substitutions.items():
        value = (raw_value or "").strip()
        if not value:
            continue
        for pair in JOSA_PAIRS:
            particle = select_josa(value, pair)
            if particle is None:
                continue
            resolved[f"{key}_JOSA_{pair}"] = f"{value}{particle}"
    return resolved


def josa_base_key(name: str) -> str | None:
    """Return the base substitution key when ``name`` is a josa companion."""
    for pair in JOSA_PAIRS:
        suffix = f"_JOSA_{pair}"
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return None


def with_josa_substitutions(substitutions: Mapping[str, str]) -> dict[str, str]:
    """``substitutions`` plus their josa companions (originals win on collision)."""
    return {**josa_substitutions(substitutions), **dict(substitutions)}
