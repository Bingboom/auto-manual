"""Real family routing at the production queue boundary, without live writes."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools import process_build_queue
from tools.queue_config_resolution import validate_family_config_request


class TestWebPublishLocaleRouting(unittest.TestCase):
    def test_explicit_web_locale_resolves_real_single_language_family(self):
        for action in ('Web Publish', 'web_publish', 'web-publish'):
            for lang in ('en', 'fr'):
                with self.subTest(action=action, lang=lang):
                    path = process_build_queue.resolve_config_path_for_task(
                        model='JE-1000F', region='EU', lang=lang,
                        build_family=f'eu-{lang}', workflow_action=action,
                    )
                    self.assertEqual(f'config.eu-{lang}.yaml', path.name)

    def validate(self, family, lang, action='Web Publish', **overrides):
        path = Path(__file__).resolve().parents[1] / 'configs' / f'config.{family}.yaml'
        cfg = process_build_queue.load_config(path)
        cfg['build'].update(overrides)
        validate_family_config_request(config_path=path, cfg=cfg,
            build_family=cfg['build']['family_id'], region='EU', lang=lang,
            workflow_action=action)

    def test_legacy_whole_book_web_remains_supported(self):
        self.validate('eu', '')

    def records(self, merged=False):
        return [process_build_queue.QueueRecord(
            record_id=f'rec_web_{lang}', document_id=f'JE-1000F_EU_{lang}_test',
            document_key='JE-1000F_EU', version='test', lang=lang,
            workflow_action='Web Publish', git_ref='review/JE-1000F-EU',
            build_family='eu-merged' if merged else f'eu-{lang}',
        ) for lang in ('en', 'fr')]

    def test_real_queue_keeps_locales_in_distinct_groups(self):
        groups = process_build_queue.group_pending_queue_records(self.records())
        self.assertEqual([['rec_web_en'], ['rec_web_fr']],
                         [[r.record_id for r in g] for g in groups])
        self.assertEqual(['en', 'fr'],
                         [process_build_queue.queue_group_lang(g) for g in groups])
        for group in groups:
            process_build_queue.validate_queue_record_group(group)

    def test_merged_web_locales_fail_before_grouping(self):
        with self.assertRaisesRegex(RuntimeError, 'single-language Build_family'):
            process_build_queue.group_pending_queue_records(self.records(merged=True))

    def test_single_language_web_requires_explicit_locale(self):
        with self.assertRaisesRegex(RuntimeError, 'explicit Lang'):
            self.validate('eu-en', '')

    def test_web_locale_rejects_merged_family_or_shared_paths(self):
        for family, overrides in (
            ('eu', {}), ('eu-en', {'include_lang_in_output_path': False}),
            ('eu-en', {'queue_by_document_key': True}),
            ('eu-en', {'languages': ['en', 'fr']}),
        ):
            with self.subTest(family=family, overrides=overrides):
                with self.assertRaisesRegex(RuntimeError, 'single-language Build_family'):
                    self.validate(family, 'en', **overrides)

    def test_web_family_language_mismatch_still_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'conflicts with Lang'):
            self.validate('eu-en', 'fr')

    def test_web_family_region_mismatch_still_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'routes to region'):
            process_build_queue.resolve_config_path_for_task(
                model='JE-1000F', region='US', lang='en',
                build_family='eu-en', workflow_action='Web Publish')

    def test_print_publish_retains_whole_book_restrictions(self):
        self.validate('eu', '', 'Publish')
        for family, lang, message in (
            ('eu-en', 'en', 'must leave Lang blank'),
            ('eu', 'en', 'must leave Lang blank'),
            ('eu-en', '', 'whole-book Build_family'),
        ):
            with self.subTest(family=family, lang=lang):
                with self.assertRaisesRegex(RuntimeError, message):
                    self.validate(family, lang, 'Publish')


if __name__ == '__main__':
    unittest.main()
