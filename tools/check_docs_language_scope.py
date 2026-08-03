"""Language-scope gate: the verification half of per-model language trimming.

``tools/model_languages.py`` decides which of a family's languages a target
ships and the bundle plan drops the rest. This module proves the built
bundle agrees, the same way ``check_docs_capability`` proves the capability
filter agreed.

Two rules, both narrow on purpose:

- ``LANG_SCOPE_UNSHIPPED_LANGUAGE``: the target's scope row excludes *every*
  language its family config declares. The build fails open there (it will
  not silently change what an existing line produces), so this is the only
  place the contradiction surfaces. The live instance is
  ``configs/config.eu-uk.yaml`` — a Ukrainian-only derivative whose
  inherited default target, JE-1000F/EU, ships no Ukrainian.
- ``LANG_SCOPE_FOREIGN_SCRIPT``: a page carries the script of a language the
  scope dropped. This catches leakage that page selection cannot: a body
  page with neither a ``_<lang>`` suffix nor a ``**XX ...**`` tag (an
  authored review edit, a hand-copied block) is invisible to
  ``check_docs_lang_parity`` R2/R3 but not to a Cyrillic count.

Only *dropped* languages are counted, never every unshipped script. An EU
bundle legitimately carries a CJK literal (``占位符`` is a configured
allowed identity literal); scanning for scripts the family never declared
would turn that into noise. The failure mode being gated is specifically
"a language this family has templates for, that this model does not ship".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.check_docs_lang_parity import SCRIPT_RANGES  # noqa: E402
from tools.model_languages import (  # noqa: E402
    MODEL_LANGUAGES_CSV,
    LanguageScope,
    resolve_target_languages,
)

# A handful of characters is incidental (a product name, a quoted term); a
# leaked block is hundreds. Conservative on purpose — the historical
# incidents sat in the thousands.
MAX_DROPPED_SCRIPT_CHARS = 8


def _dropped_script_langs(scope: LanguageScope) -> list[str]:
    """Dropped languages whose script can be told apart from Latin."""
    return [lang for lang in scope.dropped if lang.strip().lower() in SCRIPT_RANGES]


def collect_language_scope_issues(
    *,
    bundle_dir: Path,
    family_langs: list[str],
    model: str,
    region: str,
    data_dir: Path,
    issue_cls,
) -> list:
    scope = resolve_target_languages(
        family_langs, model=model, region=region, data_dir=data_dir
    )
    issues: list = []

    if scope.unshipped:
        issues.append(issue_cls(
            code="LANG_SCOPE_UNSHIPPED_LANGUAGE",
            message=(
                f"{scope.document_key} ships none of the languages this family "
                f"declares ({sorted(scope.family_languages)}); "
                f"data/{MODEL_LANGUAGES_CSV} lists a disjoint set. Point the "
                "config at a model that ships this language, or correct the row"
            ),
            model=model, region=region,
            path=data_dir / MODEL_LANGUAGES_CSV,
        ))

    script_langs = _dropped_script_langs(scope)
    page_dir = bundle_dir / "page"
    if not script_langs or not page_dir.is_dir():
        return issues

    patterns = {
        lang: re.compile(f"[{SCRIPT_RANGES[lang.strip().lower()]}]")
        for lang in script_langs
    }
    for page in sorted(page_dir.glob("*.rst")):
        text = page.read_text(encoding="utf-8", errors="replace")
        for lang, pattern in patterns.items():
            hits = len(pattern.findall(text))
            if hits <= MAX_DROPPED_SCRIPT_CHARS:
                continue
            issues.append(issue_cls(
                code="LANG_SCOPE_FOREIGN_SCRIPT",
                message=(
                    f"{page.name} carries {hits} '{lang}'-script characters but "
                    f"{scope.document_key} ships {list(scope.languages)} — "
                    f"'{lang}' was dropped per data/{MODEL_LANGUAGES_CSV}"
                ),
                model=model, region=region, lang=lang, path=page,
            ))
    return issues
