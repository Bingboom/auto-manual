from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

VALID_FORMATS = {"html", "word", "pdf", "md"}
VALID_PDF_MODES = {"latex", "word"}
VALID_SOURCE_MODES = {"auto", "runtime", "review"}
_TEMPLATE_TOKEN_RE = re.compile(r"\{([a-z_]+)\}")
MANUAL_META_FILE_NAME = "manual_meta.json"
SWITCHER_BLOCK_START = "<!-- HB_MANUAL_SWITCHER_START -->"
SWITCHER_BLOCK_END = "<!-- HB_MANUAL_SWITCHER_END -->"
BODY_SWITCHER_CLASS = "hb-manual-switcher-body"
_REMOVE_TREE_RETRY_DELAYS = (0.2, 0.5, 1.0)
_SWITCHER_BLOCK_RE = re.compile(
    rf"{re.escape(SWITCHER_BLOCK_START)}.*?{re.escape(SWITCHER_BLOCK_END)}",
    re.DOTALL,
)
_BODY_TAG_RE = re.compile(r"<body\b([^>]*)>", re.IGNORECASE)
_MANUAL_COVER_SECTION_RE = re.compile(
    r"<section class=\"manual-cover\">.*?</section>",
    re.IGNORECASE | re.DOTALL,
)
LANGUAGE_LABELS = {
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "ja": "Japanese",
}


@dataclass(frozen=True)
class BuildTarget:
    model: str | None
    region: str | None
    lang: str | None = None


@dataclass(frozen=True)
class HtmlManualVariant:
    model: str
    region: str
    lang: str
    title: str
    html_dir: Path
    html_dir_token: str
    lang_in_output_path: bool
