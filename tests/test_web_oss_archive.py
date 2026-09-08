"""Archive content identity, publication isolation and immutable retry coverage."""
from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.oss_archive_store import upload_archive
from tools.web_archive_package import digest, package_archive
from tools.web_manual_package import file_inventory, write_json
from tools.web_publish_archive import finish_web_archive, prepare_web_archive


class MemoryBucket:
    def __init__(self):
        self.objects = {}
        self.writes = []
        self.lock = threading.Lock()
        self.corrupt = False

    def object_exists(self, key):
        return key in self.objects

    def get_object(self, key):
        data = self.objects[key]
        return io.BytesIO(data + b'corrupt' if self.corrupt and key.endswith('.pdf') else data)

    def put_object(self, key, data, headers):
        with self.lock:
            if key in self.objects and headers.get('x-oss-forbid-overwrite') == 'true':
                raise RuntimeError('Object already exists')
            self.objects[key] = data
            self.writes.append(key)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        packages = {}
        for lang, other in [('en', 'fr'), ('fr', 'en')]:
            folder = self.source / lang
            folder.mkdir(parents=True)
            (folder / 'index.html').write_text(
                f'<html lang="{lang}"><a href="../{other}/index.html">Language</a>'
                '<a href="manual.pdf">PDF</a><img src="image.png"></html>')
            (folder / 'manual.pdf').write_bytes(b'%PDF-frozen')
            (folder / 'image.png').write_bytes(b'image')
            packages[lang] = {'files': file_inventory(folder)}
        write_json(self.source / 'release.json', {
            'schema_version': 'web-package-release/v1', 'model': 'Example', 'region': 'US',
            'version': '1.0', 'source_revision': 'source-sha', 'packages': packages,
        })

    def package(self):
        return package_archive(self.source, self.root / 'package')

    def test_layout_links_and_original_bytes(self):
        before = file_inventory(self.source)
        release = self.package()
        self.assertIn('../../fr/user-manual/index.html', (release / 'en/user-manual/index.html').read_text())
        self.assertEqual(before, file_inventory(self.source))
        self.assertTrue((release / 'en/user-manual/Example-user-manual-en-digital-1.0.pdf').is_file())
        self.assertFalse((release.parent.parent / 'latest').exists())

    def test_modified_input_fails_before_destination(self):
        (self.source / 'en/index.html').write_text('modified')
        with self.assertRaises(ValueError):
            self.package()
        self.assertFalse((self.root / 'package').exists())

    def test_symlink_rejected(self):
        (self.source / 'en/link').symlink_to(self.root)
        with self.assertRaises((ValueError, RuntimeError)):
            self.package()

    def test_broken_links_rejected(self):
        (self.source / 'en/index.html').write_text('<img src="missing.png">')
        metadata = json.loads((self.source / 'release.json').read_text())
        metadata['packages']['en']['files'] = file_inventory(self.source / 'en')
        write_json(self.source / 'release.json', metadata)
        with self.assertRaises(ValueError):
            self.package()

    def test_upload_retry_and_completion_last(self):
        release = self.package()
        bucket = MemoryBucket()
        first = upload_archive(release, bucket, 'portable/manuals')
        writes = list(bucket.writes)
        self.assertTrue(writes[-1].endswith('_archive-complete.json'))
        self.assertEqual(first, upload_archive(release, bucket, 'portable/manuals'))
        self.assertEqual(writes, bucket.writes)
        self.assertTrue(all('/latest/' not in key for key in writes))

    def test_conflict_before_any_write(self):
        release = self.package()
        bucket = MemoryBucket()
        bucket.objects['portable/manuals/products/Example/releases/1.0/en/user-manual/index.html'] = b'old'
        with self.assertRaises(ValueError):
            upload_archive(release, bucket, 'portable/manuals')
        self.assertEqual(bucket.writes, [])

    def test_remote_corruption_never_marks_complete(self):
        release = self.package()
        bucket = MemoryBucket()
        bucket.corrupt = True
        with self.assertRaises(ValueError):
            upload_archive(release, bucket, 'portable/manuals')
        self.assertFalse(any(k.endswith('_archive-complete.json') for k in bucket.objects))
        bucket.corrupt = False
        self.assertEqual('archived', upload_archive(release, bucket, 'portable/manuals')['status'])

    def test_region_identity_reservation_conflict(self):
        release = self.package()
        bucket = MemoryBucket()
        upload_archive(release, bucket, 'portable/manuals')
        marker = next(k for k in bucket.objects if k.endswith('_archive-reservation.json'))
        bucket.objects[marker] = b'another-region'
        previous = list(bucket.writes)
        with self.assertRaises(ValueError):
            upload_archive(release, bucket, 'portable/manuals')
        self.assertEqual(previous, bucket.writes)

    def test_unsafe_prefix_and_manifest_path(self):
        release = self.package()
        bucket = MemoryBucket()
        for prefix in ['../elsewhere', '/absolute', 'a//b', 'a/../b']:
            with self.assertRaises(ValueError):
                upload_archive(release, bucket, prefix)
        manifest = json.loads((release / 'release-manifest.json').read_text())
        manifest['files'][0]['path'] = '../escape'
        write_json(release / 'release-manifest.json', manifest)
        with self.assertRaises(ValueError):
            upload_archive(release, bucket, 'portable/manuals')
        self.assertEqual([], bucket.writes)

    def test_unmanifested_file_rejected(self):
        release = self.package()
        (release / 'credentials.json').write_text('should never upload')
        bucket = MemoryBucket()
        with self.assertRaises(ValueError):
            upload_archive(release, bucket, 'portable/manuals')
        self.assertEqual([], bucket.writes)

    def test_disabled_never_invokes_network_or_build(self):
        with patch('tools.web_publish_archive.archive_settings', return_value=None), patch('subprocess.run') as run:
            self.assertIsNone(finish_web_archive(Path('missing'), staged_md=Path('missing')))
            prepare_web_archive(config_path=Path('missing'), model='Example', region='US', version='1',
                                lang=None, data_root=None, source_repo=self.root, staged_md=self.source/'en/index.html')
            run.assert_not_called()

    def test_failed_preparation_is_separate_and_sanitized(self):
        with patch('tools.web_publish_archive.archive_settings', side_effect=RuntimeError('SECRET_DO_NOT_LOG')):
            prepare_web_archive(config_path=Path('missing'), model='Example', region='US', version='1',
                                lang=None, data_root=None, source_repo=self.root, staged_md=self.source/'en/index.html')
            report = (self.source/'archive-preparation.json').read_text()
            self.assertNotIn('SECRET_DO_NOT_LOG', report)
            result = finish_web_archive(Path('missing'), staged_md=self.source/'en/index.html')
            self.assertEqual('failed', result['status'])
            self.assertNotIn('SECRET_DO_NOT_LOG', json.dumps(result))

    def test_report_disk_failure_never_raises_into_publication(self):
        with patch('tools.web_publish_archive.archive_settings', side_effect=ValueError), patch('tools.web_publish_archive.write_json', side_effect=OSError):
            self.assertEqual('failed', finish_web_archive(Path('missing'), staged_md=self.source/'en/index.html')['status'])

    def test_prepare_uses_declared_languages_and_stages_before_cleanup(self):
        import shutil
        staged = self.root / 'web/md/manual.md'
        staged.parent.mkdir(parents=True)
        staged.write_text('# frozen')
        cfg = self.root / 'config.yaml'
        cfg.write_text('build:\n  languages: [en, fr]\n')
        def build(cmd, **kwargs):
            self.assertEqual(['en', 'fr'], cmd[cmd.index('--languages')+1:cmd.index('--work-dir')])
            self.assertEqual('review-asis', cmd[cmd.index('--source')+1])
            target = Path(cmd[cmd.index('--output-dir')+1]) / 'Example/US/1.0'
            shutil.copytree(self.source, target)
        with patch('tools.web_publish_archive.archive_settings', return_value=(self.root/'settings.json', {})), patch('subprocess.run', side_effect=build):
            prepare_web_archive(config_path=cfg, model='Example', region='US', version='1.0',
                                lang=None, data_root=None, source_repo=self.root, staged_md=staged)
        status = json.loads((staged.parent.parent/'archive-preparation.json').read_text())
        self.assertEqual('prepared', status['status'])
        self.assertTrue((staged.parent.parent/'archive-package'/status['release_relative']/'release-manifest.json').is_file())

    def test_success_hook_calls_worker_only_after_metadata(self):
        release = self.package()
        staged = self.root/'staged'
        staged.mkdir()
        md = staged/'md/manual.md'
        md.parent.mkdir()
        md.write_text('# frozen')
        import shutil
        shutil.copytree(self.root/'package', staged/'archive-package')
        write_json(staged/'archive-preparation.json', {
            'status': 'prepared', 'model': 'Example', 'region': 'US', 'version': '1.0',
            'release_relative': release.relative_to(self.root/'package').as_posix(),
            'manifest_sha256': digest(release/'release-manifest.json'),
        })
        meta = staged/'metadata.json'
        settings = self.root/'settings.json'
        def worker(cmd, **kwargs):
            write_json(Path(cmd[cmd.index('--report')+1]), {'status':'archived'})
        with patch('tools.web_publish_archive.archive_settings', return_value=(settings, {'python':'python'})), patch('subprocess.run', side_effect=worker) as run:
            self.assertEqual('failed', finish_web_archive(meta, staged_md=md)['status'])
            run.assert_not_called()
            write_json(meta, {'schema_version':'auto-manual-web-publish/v1', 'workflow_action':'Web Publish',
                              'model':'Example', 'region':'US', 'version':'1.0'})
            self.assertEqual('archived', finish_web_archive(meta, staged_md=md)['status'])
            run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
