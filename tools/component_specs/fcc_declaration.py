"""FCC is a source-content contract, independent of product allowlists."""
from collections.abc import Mapping
import fnmatch
from pathlib import Path
import re

from bs4 import BeautifulSoup

COMPONENT_ID = 'HB-SPECIAL-FCC'


def declares_fcc(soup: BeautifulSoup, source_path: Path, config: Mapping) -> bool:
    if soup.select_one('.hb-source-fcc') is not None:
        return True
    if any(h.get_text(' ', strip=True).casefold() == 'fcc'
           for h in soup.find_all(re.compile(r'^h[1-6]$'))):
        return True
    if any(fnmatch.fnmatch(source_path.stem.casefold(), str(p).casefold())
           for p in config.get('source_patterns', [])):
        return True
    # Detect an orphaned English compliance opening, not a casual FCC mention.
    return not soup.find(re.compile(r'^h[1-6]$')) and bool(re.search(r'\bcomplies with part 15 of the FCC Rules\b',
                          soup.get_text(' ', strip=True), re.IGNORECASE))


def require_fcc_component(declared: bool, component_ids, source_path: Path) -> None:
    if declared and list(component_ids).count(COMPONENT_ID) != 1:
        raise ValueError(f'{source_path}: FCC content requires exactly one {COMPONENT_ID} IR component; refusing plain-text fallback')


def require_fcc_claims(declared, claims, source_path):
    require_fcc_component(declared, (claim.spec.component_id for claim in claims), source_path)


def require_fcc_markup(declared, soup, source_path):
    require_fcc_component(declared, (node.get('data-component-id') for node in
                                    soup.select('[data-component-id="HB-SPECIAL-FCC"]')), source_path)


def check_fcc_render_input(soup, source_path, config, resolved, complete):
    declared = declares_fcc(soup, source_path, config)
    if complete:
        require_fcc_component(declared, resolved, source_path)
        require_fcc_markup(declared, soup, source_path)
    return declared
