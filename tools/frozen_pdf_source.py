"""Fresh PDF intake bound to explicit, hash-verified shared artwork.

The native PDF supplies every text field. Historical JSON supplies extraction
geometry and approved errata. Finished figure panels are opt-in, locale-bound
and hash-verified; body and table screenshots remain forbidden.
"""
from __future__ import annotations

from copy import deepcopy
import json
import re
from pathlib import Path
import shutil

from tools.component_specs.overview_instance import (
    overview_instance_sha256, resolve_overview_instance, validate_resolved_overview_instance,
)
from tools.frozen_ai_source import FrozenBook
from tools.frozen_pdf_app import APP_ASSET_KEYS, app_section
from tools.frozen_pdf_glyphs import recover_pdf_glyphs, recover_recorded_glyphs
from tools.frozen_pdf_intake import load_pdf_book, read_recipe_json
from tools.frozen_pdf_media import MEDIA_ASSET_KEYS, consumed_media_regions, media_section, operation_panels
from tools.frozen_pdf_lcd import LCD_ICON_ASSET_KEYS, lcd_icon_flow
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.web_presentation import load_web_manual_contract


_REFERENCE_IDS = {'ups_connection', 'ac_wall_charging', 'solar_single', 'solar_four', 'car_charging'}


def _repair_label_wrapping(data, language):
    # Exact native extraction whitespace only. These are formatting repairs,
    # distinct from approved edits to the author's wording.
    fixes = {
        'uk': {'Режим енергозбережен ня акумулятора': 'Режим енергозбереження акумулятора'},
        'nl': {'Zonne-energie- oplaadindicator': 'Zonne-energie-oplaadindicator',
               'Batterijbespar ingsmodus': 'Batterijbesparingsmodus',
               'Batterijstroom -indicator': 'Batterijstroom-indicator',
               'Energiebespa ringsmodus': 'Energiebesparingsmodus'},
    }
    for row in data['records']['lcd_indicators']['rows']:
        before = row['label']
        after = fixes.get(language, {}).get(before)
        if after:
            row['label'] = after
            data['provenance']['corrections_applied'].append({
                'field': f"lcd/{row['number']}/label", 'physical_page': row['physical_page'],
                'bbox': row['label_bbox'], 'before': before, 'after': after,
                'reason': 'Join native PDF word fragments separated by print line wrapping',
            })


def _overview_binding(bindings: dict, target: dict) -> dict:
    """Resolve only this frozen source's optional artwork-coordinate override."""
    model, region = target['model'], target['region']
    if 'overview_instance' not in bindings:
        if 'overview_instance_sha256' in bindings:
            raise ValueError('overview instance hash has no bound instance')
        return resolve_overview_instance(model=model, region=region)
    instance = deepcopy(bindings['overview_instance'])
    issues = validate_resolved_overview_instance(instance)
    if issues:
        raise ValueError('invalid frozen overview instance: ' + '; '.join(issues))
    if instance['target'] != {'model': model, 'region': region}:
        raise ValueError('frozen overview instance target disagrees with PDF')
    if bindings.get('overview_instance_sha256') != overview_instance_sha256(instance):
        raise ValueError('frozen overview instance SHA-256 mismatch')
    return instance


def _recover_source_data(book, data, pdf_path, original, language):
    ai = pdf_path.parent / original['original_source']['filename']
    if not book.target_layout:
        return recover_pdf_glyphs(data, ai)
    recovery_path = 'source/glyph_recoveries.json'
    if any(entry['path'] == recovery_path for entry in original['inputs']):
        ledger = book.read(recovery_path)
        if ledger.get('target') != {key: book.target[key] for key in ('model', 'region')}:
            raise ValueError('native glyph recovery target disagrees with source')
        return recover_recorded_glyphs(data, ledger, language)
    if any(character in str(data) for character in ('\x00', '\x1f', '\ufffd')):
        raise ValueError('unresolved native glyph requires target-local recovery evidence')
    return data


def _bind_source_figures(book, bindings, language, reference_ids):
    recipes = book.read(f'source/{language}_figure_manifest.json')['figures']
    selected = bindings.get('figures', [])
    reference_bindings = {figure['slug']: figure for figure in selected}
    if len(reference_bindings) != len(selected) or set(reference_bindings) != reference_ids:
        raise ValueError('governed reference artwork must cover UPS and all four charging diagrams')
    book.figures = [{**{key: figure[key] for key in ('slug', 'section_id', 'physical_page', 'clip_points')},
                     'asset_key': reference_bindings[figure['slug']]['asset_key'],
                     'presentation': 'textless-shared-art'}
                    for figure in recipes if figure['slug'] in reference_ids]
    if len(book.figures) != len(reference_ids) or {f['slug'] for f in book.figures} != reference_ids:
        raise ValueError('source geometry must contain exactly the five required reference diagrams')
    return reference_bindings


def _required_asset_keys(book, bindings):
    media_keys = book.target_layout.get('media_asset_keys', MEDIA_ASSET_KEYS)
    lcd_rows = book.target_layout.get('lcd_rows')
    lcd_keys = ([f"lcd.icon.{row['icon_id']}" for row in lcd_rows] if lcd_rows else
                book.target_layout.get('lcd_icon_asset_keys', LCD_ICON_ASSET_KEYS))
    return {*APP_ASSET_KEYS, *media_keys, *lcd_keys, 'lcd.mode', 'lcd.map',
            *(f"symbol.{row['icon_id']}" for row in book.records['symbols']['pictograms']),
            *(figure['asset_key'] for figure in bindings.get('figures', []))}


def _allowed_asset_modes(layout):
    modes = {'textless', 'fixed-product-markings', 'app-ui'}
    if layout.get('allow_source_finished_panels'):
        modes.add('source-finished-panel')
    return modes


class PdfBook(FrozenBook):
    """Use the shared semantic table helpers with a fresh source and asset map."""

    source_kind = "frozen-pdf-json"

    def __init__(self, pdf_path: Path, recipe_root: Path, assets_manifest: Path,
                 output: Path, language: str):
        self.source_root, self.output, self.language = recipe_root.resolve(), output.resolve(), language
        original = self.read('source_manifest.json')
        self.target = deepcopy(original['target'])
        self.errata = self.read('source/errata.json')
        bindings = json.loads(assets_manifest.read_text(encoding='utf-8'))
        text_source = {'filename': pdf_path.name, 'sha256': file_sha256(pdf_path)}
        if bindings.get('text_source') != text_source:
            raise ValueError('artwork manifest text_source disagrees with PDF identity')
        data = load_pdf_book(pdf_path, language, recipe_root)
        self.target_layout = data.get('target_layout') or {}
        data = _recover_source_data(self, data, pdf_path, original, language)
        _repair_label_wrapping(data, language)
        for key in ('source', 'index', 'locale', 'records', 'front_back', 'provenance'):
            setattr(self, key, data[key])
        if bindings['target'] != {key: self.target[key] for key in ('model', 'region')}:
            raise ValueError('artwork target disagrees with PDF')
        version = bindings.get('technical_version', '')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', version) or version == self.target['technical_version']:
            raise ValueError('fresh PDF artwork requires a new immutable technical_version')
        self.target['technical_version'] = version
        if bindings.get('pending'):
            raise ValueError('artwork remains pending: ' + ', '.join(bindings['pending']))
        reference_ids = set(self.target_layout.get('reference_ids', _REFERENCE_IDS))
        reference_bindings = _bind_source_figures(self, bindings, language, reference_ids)
        required = _required_asset_keys(self, bindings)
        missing = sorted(required - bindings['assets'].keys())
        if missing:
            raise ValueError('missing governed artwork: ' + ', '.join(missing))
        self.hashes, self.assets = {}, {}
        for key, record in bindings['assets'].items():
            source = (assets_manifest.parent / record['path']).resolve()
            if file_sha256(source) != record['sha256']:
                raise ValueError(f'governed artwork changed: {key}')
            if record['content_mode'] not in _allowed_asset_modes(self.target_layout):
                raise ValueError(f'body text or table image is forbidden: {key}')
            destination = f"assets/{record['sha256'][:12]}_{source.name}"
            self.assets[key] = {**record, 'asset_ref': destination}
        from tools.frozen_pdf_reference import bind_reference_labels
        bind_reference_labels(self, reference_bindings)
        reference_overview = self.target_layout.get('media', {}).get('overview', {}).get('presentation') == 'reference-figures'
        self.overview_instance = None if reference_overview else _overview_binding(bindings, self.target)
        from tools.frozen_pdf_finished_overview import bind_finished_overview
        bind_finished_overview(self, bindings, assets_manifest)
        # Validate the whole binding before creating output or copying files.
        for key, record in self.assets.items():
            source = (assets_manifest.parent / record['path']).resolve()
            destination = output / record['asset_ref']
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            self.hashes[record['asset_ref']] = record['sha256']
        self.contract = load_web_manual_contract(model=self.target['model'], region=self.target['region'])
        self.contract = deepcopy(bindings.get('web_contract', self.contract))
        self.expected_reference_count = len(reference_ids) + 2  # LCD map and live-caption App result
        for figure in self.figures:
            figure['presentation'] = 'textless-shared-art'
        self.art = {f['slug']: self.assets[f['asset_key']] for f in self.figures}
        self.art['lcd_mode_art'] = self.assets['lcd.mode']
        self.icon_refs = [self.assets[f"symbol.{row['icon_id']}"]['asset_ref']
                          for row in self.records['symbols']['pictograms']]
        self.manifest = {
            'schema_version': 'auto-manual-frozen-web-source/v1', 'target': self.target,
            'original_source': original['original_source'], 'text_source': self.provenance['pdf'],
            'intake_method': 'fresh-native-pdf-text',
            'geometry_recipe_sha256': file_sha256(recipe_root / 'source_manifest.json'),
            'source_records_sha256': value_sha256(data),
            'artwork_manifest_sha256': file_sha256(assets_manifest),
        }

    def read(self, path):
        if path == 'source_manifest.json':
            return super().read(path)
        return read_recipe_json(self.source_root, path)

    def media_section(self, section):
        if (section == 'product_overview' and
                self.target_layout.get('media', {}).get('overview', {}).get('presentation') == 'reference-figures'):
            return []
        return media_section(self, section, self.assets)

    def operation_panels(self):
        return operation_panels(self, self.assets)

    def consumed_media_regions(self):
        from tools.frozen_pdf_reference import reference_label_regions
        return [*consumed_media_regions(self), *reference_label_regions(self.figures)]

    def figure(self, figure):
        # A local source panel is not an approved composite. Its embedded
        # captions retain native semantic copy without a duplicate visible row.
        from tools.frozen_pdf_app import artwork_node
        asset = self.assets[figure['asset_key']]
        if figure.get('live_captions'):
            from tools.frozen_pdf_reference import labeled_artwork_node
            return labeled_artwork_node(figure, asset['asset_ref'], self.language)
        source_captions = self.records.get('reference_captions', {}).get(figure['slug'])
        if source_captions:
            if source_captions['physical_page'] != figure['physical_page']:
                raise ValueError(f"{figure['slug']}: native caption page changed")
            if (asset.get('content_mode') == 'source-finished-panel' and
                    asset.get('captions_embedded') is True):
                from tools.frozen_pdf_reference import finished_artwork_node
                return finished_artwork_node(figure, asset, source_captions, self.language)
            return artwork_node(asset['asset_ref'], figure['slug'], self.language,
                                f"{self.language}/pdf-page-{figure['physical_page']}#{figure['slug']}",
                                captions=[item['text'] for item in source_captions['labels']])
        semantic_copy = ''
        if figure['section_id'] == 'product_overview' and self.target_layout.get('media', {}).get('overview', {}).get('presentation') == 'reference-figures':
            view = figure['slug'].removeprefix('overview_').removesuffix('_view')
            record = self.records['media']['overview']['views'][view]
            semantic_copy = ' '.join([self.correct(record['caption']), *(
                self.correct(value['text']) for value in record['callouts'].values())])
            accessibility_label = self.correct(record['caption'])
        else:
            accessibility_label = None
        return artwork_node(asset['asset_ref'], figure['slug'], self.language,
                            f"{self.language}/pdf-page-{figure['physical_page']}#{figure['slug']}",
                            accessibility_label=accessibility_label, semantic_copy=semantic_copy)

    def special(self, section):
        if section == 'safety':
            from tools.frozen_pdf_frontmatter import positioned_safety_flow, safety_flow
            return positioned_safety_flow(self) if 'safety' in self.records else safety_flow(self)
        if section == 'app_setup':
            return app_section(self, self.assets)
        if section == 'lcd_display':
            from tools.frozen_pdf_app import artwork_node
            title = self.locale['titles'][self.index['section_ids'].index(section)]
            return [artwork_node(self.assets['lcd.map']['asset_ref'], 'lcd-map', self.language,
                                 f'{self.language}/lcd-display'),
                    *lcd_icon_flow(self.records['lcd_indicators'], assets=self.assets,
                                   accessibility_label=title, source_ref=f'{self.language}/lcd-display#icons',
                                   language=self.language,
                                   row_bindings=tuple((row['number'], row['icon_id']) for row in self.target_layout['lcd_rows'])
                                   if 'lcd_rows' in self.target_layout else None)]
        return super().special(section)
