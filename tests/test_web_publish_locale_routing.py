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


class TestUsSingleLanguageWebNaming(unittest.TestCase):
    """JE-1000F/US pilot: three real configs, one already-published English URL."""

    CONFIGS = Path(__file__).resolve().parents[1] / 'configs'

    def md_output(self, lang, family=None):
        return process_build_queue.resolve_md_output_path_for_target(
            config_path=self.CONFIGS / f'config.{family or f"us-{lang}"}.yaml',
            model='JE-1000F', region='US', lang=lang,
        )

    def test_explicit_us_locale_resolves_real_single_language_family(self):
        for lang in ('en', 'fr', 'es'):
            with self.subTest(lang=lang):
                path = process_build_queue.resolve_config_path_for_task(
                    model='JE-1000F', region='US', lang=lang,
                    build_family=f'us-{lang}', workflow_action='Web Publish',
                )
                self.assertEqual(f'config.us-{lang}.yaml', path.name)

    def test_us_single_language_configs_satisfy_the_web_locale_contract(self):
        for lang in ('en', 'fr', 'es'):
            path = self.CONFIGS / f'config.us-{lang}.yaml'
            cfg = process_build_queue.load_config(path)
            with self.subTest(lang=lang):
                validate_family_config_request(config_path=path, cfg=cfg,
                    build_family=f'us-{lang}', region='US', lang=lang,
                    workflow_action='Web Publish')

    def test_english_web_route_keeps_the_published_markdown_stem(self):
        path = self.md_output('en')
        self.assertEqual('manual_je1000f_us.md', path.name)
        self.assertEqual(('JE-1000F', 'US', 'en', 'md'), path.parts[-5:-1])

    def test_sibling_locales_carry_distinct_markdown_stems(self):
        stems = {lang: self.md_output(lang).stem for lang in ('en', 'fr', 'es')}
        self.assertEqual({'en': 'manual_je1000f_us', 'fr': 'manual_je1000f_us_fr',
                          'es': 'manual_je1000f_us_es'}, stems)
        # Two manuals sharing one stem are rejected as a duplicate RTD short alias.
        self.assertEqual(3, len(set(stems.values())))

    def test_print_artefacts_keep_their_language_suffix(self):
        for lang in ('en', 'fr', 'es'):
            with self.subTest(lang=lang):
                word = process_build_queue.resolve_word_output_path_for_target(
                    config_path=self.CONFIGS / f'config.us-{lang}.yaml',
                    model='JE-1000F', region='US', lang=lang,
                )
                self.assertEqual(f'manual_je1000f_us_{lang}.docx', word.name)

    def test_merged_us_book_keeps_its_own_build_root(self):
        merged = self.md_output(None, family='us')
        self.assertEqual('manual_je1000f_us.md', merged.name)
        self.assertEqual(('JE-1000F', 'US', 'md'), merged.parts[-4:-1])
        self.assertNotEqual(merged, self.md_output('en'))


if __name__ == '__main__':
    unittest.main()
