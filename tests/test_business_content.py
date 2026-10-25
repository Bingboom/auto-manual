from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

import yaml

from scripts.check_business_content import check, validate_publish


ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = "${{ github.repository == 'Bingboom/auto-manual' }}"
BUSINESS = "Bingboom/Hello-Docs"
REVIEW = "Bingboom/Hello-Docs-Review"


class WorkflowRoutingTests(unittest.TestCase):
    def test_engineering_lanes_keep_their_triggers_but_never_allocate_mirror_runners(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/manual-validation.yml').read_text())
        jobs = workflow['jobs']
        engineering = set(jobs) - {'secret-scan', 'business-content'}
        self.assertEqual(len(engineering), 16)
        for name in engineering:
            self.assertEqual(jobs[name]['if'], ENGINEERING, name)
        self.assertNotIn('if', jobs['secret-scan'])
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        self.assertEqual(jobs['business-content']['if'],
                         "${{ github.repository == 'Bingboom/Hello-Docs' || github.repository == 'Bingboom/Hello-Docs-Review' }}")
        self.assertEqual(set(workflow[True]), {'push', 'pull_request'})
        for name in ['nightly-render', 'review-preview', 'manifest-regenerate-diff']:
            other = yaml.safe_load((ROOT / f'.github/workflows/{name}.yml').read_text())
            self.assertEqual(len(other['jobs']), 1)
            self.assertEqual(next(iter(other['jobs'].values()))['if'], ENGINEERING)

    def test_content_gate_uses_trusted_base_for_prs_and_needs_no_secrets_or_packages(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/manual-validation.yml').read_text())
        content = workflow['jobs']['business-content']
        serialized = json.dumps(content)
        self.assertNotIn('secrets.', serialized)
        self.assertNotIn('pip install', serialized)
        self.assertEqual(content['steps'][0]['with']['fetch-depth'], 1)
        self.assertIn('/docs/publish/', content['steps'][0]['with']['sparse-checkout'])
        run = content['steps'][-1]['run']
        self.assertIn('git show "$CONTENT_BASE:scripts/check_business_content.py"', run)
        self.assertIn('--pr', run)


class ContentChecksTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.write('engine.txt', 'source')
        self.commit()
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout

    def write(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)
        return p

    def commit(self):
        self.git('add', '.')
        self.git('commit', '--allow-empty', '-m', 'fixture')

    def test_owned_content_pr_and_engineering_mirror_push(self):
        self.write('docs/knowledge/data.json', '{"status":"existing"}')
        self.commit()
        check(self.root, BUSINESS, base=self.base, pr=True)
        self.write('engine.txt', 'new engine')
        self.commit()
        check(self.root, BUSINESS, base=self.base)  # mirror sync may change engineering
        with self.assertRaisesRegex(ValueError, 'only owned content'):
            check(self.root, BUSINESS, base=self.base, pr=True)

    def test_rename_out_of_owned_content_cannot_hide_engineering_change(self):
        self.write('docs/knowledge/old.json', '{}')
        self.commit()
        base = self.git('rev-parse', 'HEAD').strip()
        self.git('mv', 'docs/knowledge/old.json', 'unowned.json')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'only owned content'):
            check(self.root, BUSINESS, base=base, pr=True)

    def test_review_content_stays_private_and_cannot_edit_mirrored_review_bundles(self):
        self.write('docs/review-drafts/EXAMPLE/US/metadata.json', '{"status":"draft"}')
        self.commit()
        check(self.root, REVIEW, base=self.base, pr=True)
        self.write('docs/_review/example/page.rst', 'not workbench-owned')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'only owned content'):
            check(self.root, REVIEW, base=self.base, base_ref='review/example', pr=True)

    def test_review_backport_only_accepts_review_base(self):
        self.write('docs/_review/example/page.rst', 'Reviewed content')
        self.commit()
        check(self.root, BUSINESS, base=self.base, base_ref='review/example', pr=True)
        with self.assertRaises(ValueError):
            check(self.root, BUSINESS, base=self.base, base_ref='main', pr=True)

    def test_other_mirror_content_is_rejected_even_on_push(self):
        for repository, path in [(BUSINESS, 'docs/review-drafts/draft.html'),
                                 (REVIEW, 'docs/knowledge/data.json')]:
            with self.subTest(repository=repository):
                self.write(path, '{}')
                self.commit()
                with self.assertRaisesRegex(ValueError, 'other mirror'):
                    check(self.root, repository, base=self.base)
                self.git('rm', path)
                self.commit()

    def test_invalid_json_and_csv_fail_and_deleted_json_is_allowed(self):
        p = self.write('docs/knowledge/data.json', '{broken')
        self.commit()
        with self.assertRaises(ValueError):
            check(self.root, BUSINESS, base=self.base)
        p.unlink()
        self.commit()
        check(self.root, BUSINESS, base=self.base)
        self.write('docs/knowledge/table.csv', 'column\n"unterminated')
        self.commit()
        import csv
        with self.assertRaises(csv.Error):
            check(self.root, BUSINESS, base=self.base)

    def test_workflow_shell_fetches_missing_base_in_a_shallow_content_checkout(self):
        import os
        self.write('scripts/check_business_content.py',
                   (ROOT / 'scripts/check_business_content.py').read_text())
        self.commit()
        base = self.git('rev-parse', 'HEAD').strip()
        self.write('docs/knowledge/data.json', '{"source":"frozen"}')
        self.commit()
        workflow = yaml.safe_load((ROOT / '.github/workflows/manual-validation.yml').read_text())
        shell = workflow['jobs']['business-content']['steps'][-1]['run']
        with TemporaryDirectory() as other:
            clone = Path(other) / 'mirror'
            subprocess.run(['git', 'clone', '--depth=1', self.root.as_uri(), str(clone)],
                           check=True, capture_output=True)
            env = dict(os.environ, CONTENT_REPOSITORY=BUSINESS, CONTENT_BASE=base,
                       CONTENT_BASE_REF='main', CONTENT_EVENT='pull_request', RUNNER_TEMP=other)
            result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', shell],
                                    cwd=clone, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Business content checks passed', result.stdout)

    def test_trusted_base_checker_rejects_a_pr_that_replaces_its_checker(self):
        self.write('scripts/check_business_content.py',
                   (ROOT / 'scripts/check_business_content.py').read_text())
        self.commit()
        base = self.git('rev-parse', 'HEAD').strip()
        self.write('scripts/check_business_content.py', 'raise SystemExit(0)')
        self.write('engine.txt', 'unreviewed engineering change')
        self.commit()
        import sys
        with TemporaryDirectory() as trusted:
            script = Path(trusted) / 'check_business_content.py'
            script.write_text(self.git('show', f'{base}:scripts/check_business_content.py'))
            result = subprocess.run([sys.executable, str(script), '--repository', BUSINESS,
                                     '--base', base, '--pr'], cwd=self.root,
                                    capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('only owned content', result.stderr)

    def test_missing_pr_base_and_symlink_fail_closed(self):
        with self.assertRaises(ValueError):
            check(self.root, BUSINESS, pr=True)
        dest = self.root / 'docs/knowledge/link.json'
        dest.parent.mkdir(parents=True)
        dest.symlink_to(self.root / 'engine.txt')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'symlink'):
            check(self.root, BUSINESS, base=self.base, pr=True)


class PublishIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.relative = 'web/EXAMPLE/US/en/md/manual.md'
        p = self.root / self.relative
        p.parent.mkdir(parents=True)
        p.write_bytes(b'Approved content\n')
        self.manifest = {
            'schema_version': 'auto-manual-web-publish-branch/v2',
            'targets': [{'model': 'EXAMPLE', 'region': 'US', 'lang': 'en',
                         'route': 'EXAMPLE/US/en/md', 'manual': 'manual.md'}],
            'files': [{'path': self.relative, 'size': p.stat().st_size,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}],
        }
        self.save()

    def save(self):
        (self.root / 'publish_manifest.json').write_text(json.dumps(self.manifest))

    def test_valid_and_corrupted_file(self):
        validate_publish(self.root)
        (self.root / self.relative).write_text('tampered content')
        with self.assertRaisesRegex(ValueError, 'size/hash'):
            validate_publish(self.root)

    def test_unlisted_file_and_missing_file(self):
        extra = self.root / 'unlisted.txt'
        extra.write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            validate_publish(self.root)
        extra.unlink()
        (self.root / self.relative).unlink()
        with self.assertRaisesRegex(ValueError, 'missing file'):
            validate_publish(self.root)

    def test_schema_empty_targets_duplicates_and_escaping_paths(self):
        for mutation in ['schema', 'empty', 'duplicate', 'escape', 'absolute']:
            with self.subTest(mutation=mutation):
                original = json.loads(json.dumps(self.manifest))
                if mutation == 'schema': self.manifest['schema_version'] = 'unknown'
                if mutation == 'empty': self.manifest['targets'] = []
                if mutation == 'duplicate': self.manifest['targets'] *= 2
                if mutation == 'escape': self.manifest['files'][0]['path'] = '../outside'
                if mutation == 'absolute': self.manifest['files'][0]['path'] = '/etc/hosts'
                self.save()
                with self.assertRaises(ValueError):
                    validate_publish(self.root)
                self.manifest = original

    def test_same_size_corruption_and_duplicate_inventory(self):
        p = self.root / self.relative
        p.write_bytes(b'X' * p.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'size/hash'):
            validate_publish(self.root)
        self.manifest['files'][0]['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
        self.manifest['files'] *= 2
        self.save()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate_publish(self.root)


if __name__ == '__main__':
    unittest.main()
