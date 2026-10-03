"""Acceptance cases for frozen source freshness, safe retries and release identity."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stdout

from tools import workspace_snapshot as snap
from tools import workspace_refresh as refresh
from tools import workspace_refresh_verify as verify
from tools.workspace_refresh_trigger import REQUEST_ENV, delivery_readback, request_refresh
from tools.workspace_freshness import freshness, inventory
from tools.rtd_deliverables import snapshot_problems
from tests.test_rtd_deliverables import snapshot
from tests.test_rtd_system_workspace import corpus_contract


class CompleteReadTests(unittest.TestCase):
    def page(self, count=1, start=0):
        return {"data": {"fields": ["Text"], "data": [["value"] for _ in range(count)],
                         "record_id_list": [f"r{i}" for i in range(start, start + count)]}}

    def test_legitimate_empty_has_explicit_schema_and_id_list(self):
        self.assertEqual(snap.complete_rows(lambda _: self.page(0), "base", "table"), (["Text"], []))

    def test_missing_data_is_failure_not_empty(self):
        for payload in ({"data": {"fields": ["Text"]}}, {"code": 999, "data": self.page(0)["data"]},
                        {"data": {"fields": ["Text"], "data": []}}):
            with self.subTest(payload=payload), self.assertRaises(RuntimeError):
                snap.complete_rows(lambda _: payload, "base", "table")

    def test_page_failure_and_duplicate_page_are_rejected(self):
        for reader in (Mock(side_effect=[self.page(200), RuntimeError("network")]),
                       Mock(side_effect=[self.page(200), self.page(200)])):
            with self.assertRaises(RuntimeError):
                snap.complete_rows(reader, "base", "table")

    def test_early_end_and_schema_drift_rejected(self):
        page = self.page(1)
        page["data"]["has_more"] = True
        with self.assertRaises(RuntimeError):
            snap.complete_rows(lambda _: page, "base", "table")
        page = self.page(0)
        page["data"]["fields"] = ["Changed"]
        with self.assertRaises(RuntimeError):
            snap.complete_rows(Mock(side_effect=[self.page(200), page]), "base", "table")

    def test_complete_two_pages_keeps_all_identities(self):
        reader = Mock(side_effect=[self.page(200), self.page(2, 200)])
        self.assertEqual(len(snap.complete_rows(reader, "base", "table")[1]), 202)


class SnapshotSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "snapshot.json"
        self.previous = snapshot()
        snap.atomic_json(self.path, self.previous)
        self.original = self.path.read_bytes()

    def save(self, candidate, previous=None):
        return snap.save_snapshot(self.path, candidate, previous=previous or self.previous,
                                  validate=snapshot_problems, source={"identity_sha256": "1" * 64})

    def test_unchanged_read_logs_without_rewriting_timestamp(self):
        candidate = dict(self.previous, exported_at="2026-10-02")
        result = self.save(candidate)
        self.assertEqual(result["status"], "unchanged")
        self.assertIn("checked_at", result)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_changed_delivery_is_atomic_and_retry_is_noop(self):
        candidate = copy.deepcopy(self.previous)
        candidate["documents"][0]["formats"]["word"]["version"] = "3.0"
        self.assertEqual(self.save(candidate)["status"], "changed")
        saved = json.loads(self.path.read_text())
        first = self.path.read_bytes()
        self.assertEqual(self.save(candidate, saved)["status"], "unchanged")
        self.assertEqual(first, self.path.read_bytes())

    def test_clear_or_missing_delivery_never_overwrites_previous(self):
        for docs in ([], self.previous["documents"][:-1]):
            with self.assertRaises(ValueError):
                self.save(dict(self.previous, documents=docs))
            self.assertEqual(self.path.read_bytes(), self.original)

    def test_atomic_replace_failure_preserves_previous(self):
        candidate = copy.deepcopy(self.previous)
        candidate["documents"][0]["formats"]["word"]["version"] = "3"
        with patch("tools.workspace_snapshot.os.replace", side_effect=OSError("disk")), self.assertRaises(OSError):
            self.save(candidate)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_source_change_rejected(self):
        prior = dict(self.previous, refresh={"source": {"identity_sha256": "other"}})
        with self.assertRaises(ValueError):
            self.save(self.previous, prior)


class FreshnessTests(unittest.TestCase):
    def test_fresh_build_does_not_make_old_data_fresh_and_failure_keeps_numbers(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = snap.data_dir(root) / snap.NAMES["deliverables"]
            snap.atomic_json(path, snapshot())
            registry = {"deliverables_feishu": {"stale_after_days": 3}, "corpus": {"stale_after_days": 7}}
            rows = freshness(root, registry, dt.date(2026, 10, 2))
            self.assertEqual(rows[0]["state"], "待更新")
            self.assertEqual(rows[1]["state"], "Unavailable")
            snap.atomic_json(path.parent / "deliverables-status.json", {"status": "failed"})
            rows = freshness(root, registry, dt.date(2026, 10, 2))
            self.assertEqual(rows[0]["state"], "更新失败 · 沿用旧数据")
            self.assertEqual(json.loads(path.read_text())["documents"], snapshot()["documents"])


class TriggerTests(unittest.TestCase):
    def test_writeback_must_read_back_before_request(self):
        source = Mock()
        binding = SimpleNamespace(base_token="base", table_id="table")
        group = [SimpleNamespace(record_id="rec1")]
        expected = {"idml_file": "https://t.feishu.cn/wiki/one"}
        with patch.dict(os.environ, {REQUEST_ENV: "enabled"}):
            source.fetch_records_with_ids.return_value = [{"record_id": "rec1", "fields": {}}]
            with self.assertRaises(RuntimeError):
                delivery_readback(source, binding, group, expected)
            source.fetch_records_with_ids.return_value = [{"record_id": "rec1", "fields": expected}]
            self.assertEqual(delivery_readback(source, binding, group, expected), ["rec1"])

    def test_same_batch_is_deduplicated(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {REQUEST_ENV: str(Path(tmp) / "request.json")}):
            request_refresh("deliverables", ["r2", "r1", "r1"])
            first = Path(os.environ[REQUEST_ENV]).read_bytes()
            request_refresh("deliverables", ["r1", "r2"])
            self.assertEqual(first, Path(os.environ[REQUEST_ENV]).read_bytes())
            self.assertEqual(json.loads(first)["identities"], ["r1", "r2"])

    def test_tm_dry_run_and_failure_do_not_trigger(self):
        from tools.translation_memory_sync import apply_translation_suggestions
        from tests.test_translation_memory_sync import _FakeTm, _sug, _tm
        transport = _FakeTm([_tm("rec1", en="Hello", it="Vecchio")])
        with patch("tools.workspace_refresh_trigger.request_refresh") as trigger:
            apply_translation_suggestions([_sug()], approved_hashes={"t1"}, transport=transport, write=False)
            trigger.assert_not_called()
            apply_translation_suggestions([_sug()], approved_hashes={"t1"}, transport=transport, write=True)
            trigger.assert_called_once()


class ReleaseTests(unittest.TestCase):
    def test_export_success_or_receipt_alone_is_not_online_confirmation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = inventory(root)
            html = b'<span data-workspace-source="deliverables" data-snapshot-sha256=""></span><span data-workspace-source="corpus" data-snapshot-sha256=""></span>'
            receipt = {"workspace_revision": "target", "workspace_sources": expected,
                       "files": {verify.ROUTE: hashlib.sha256(html).hexdigest()}}
            def fetch(url):
                return json.dumps(receipt).encode() if url.endswith("manual-deployment.json") else html
            with patch.object(verify, "command", return_value=""):
                self.assertEqual(verify.verify_once(root, "target", fetch=fetch)["status"], "verified")
                with self.assertRaises(ValueError):
                    verify.verify_once(root, "other", fetch=fetch)
                receipt["files"][verify.ROUTE] = "0" * 64
                with self.assertRaises(ValueError):
                    verify.verify_once(root, "target", fetch=fetch)


class ExportServiceTests(unittest.TestCase):
    def test_read_failure_preserves_valid_snapshot_and_redacts_error(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "tools" / "rtd_portal_assets"
            snap.atomic_json(assets / snap.NAMES["deliverables"], snapshot())
            secret = "must-never-appear"
            with patch.dict(os.environ, {"FEISHU_PHASE2_BASE_TOKEN": secret,
                                        "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID": "build",
                                        "FEISHU_PHASE2_MODEL_CAPABILITIES_TABLE_ID": "key"}), redirect_stdout(io.StringIO()) as out:
                result = refresh.refresh("deliverables", root=root, log=root / "result.json", cli_bin="unused", identity="bot",
                                         run=Mock(side_effect=RuntimeError(secret)))
            self.assertEqual(result["status"], "failed")
            self.assertNotIn(secret, out.getvalue())
            self.assertEqual(json.loads((assets / snap.NAMES["deliverables"]).read_text())["documents"], snapshot()["documents"])

    def test_corpus_revision_changes_hash_without_changing_counts(self):
        from tools.rtd_system_workspace import corpus_export
        def reader(text):
            return lambda _: {"data": {"fields": ["en", "fr", "Status"], "record_id_list": ["r1"], "data": [["Hello", text, "Approved"]]}}
        a = corpus_export(corpus_contract(), base_token="base", run=reader("Bonjour"), today=dt.date(2026, 10, 2))
        b = corpus_export(corpus_contract(), base_token="base", run=reader("Salut"), today=dt.date(2026, 10, 2))
        self.assertEqual(a["sentence_pairs"], b["sentence_pairs"])
        self.assertNotEqual(snap.content_digest(a), snap.content_digest(b))
        self.assertNotIn("Bonjour", json.dumps(a))


class SubmissionTests(unittest.TestCase):
    def test_timestamp_only_confirmations_are_equivalent(self):
        from tools.workspace_refresh_publish import equivalent
        with TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
            base = {"status": "changed", "stage": "snapshot-validated", "content_sha256": "a", "checked_at": "old"}
            snap.atomic_json(a, base)
            snap.atomic_json(b, dict(base, status="unchanged", checked_at="new"))
            self.assertTrue(equivalent(a, b))
            snap.atomic_json(a, dict(base, status="failed", stage="source-read"))
            self.assertFalse(equivalent(a, b))

    def test_no_change_does_not_push_or_open_pr(self):
        from tools import workspace_refresh_publish as publisher
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snap.atomic_json(snap.data_dir(root) / "deliverables-status.json", {"status": "unchanged", "stage": "snapshot-validated"})
            def execute(args, cwd=None):
                if args[:3] == ["gh", "pr", "list"]:
                    return "[]"
                return ""
            with patch.object(publisher, "command", side_effect=execute) as runner:
                self.assertEqual(publisher.submit(root, "deliverables"), "no-change")
                self.assertFalse(any("push" in call.args[0] or "commit" in call.args[0] for call in runner.call_args_list))

    def test_foreign_branch_paths_block_submission(self):
        from tools import workspace_refresh_publish as publisher
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snap.atomic_json(snap.data_dir(root) / "deliverables-status.json", {"status": "changed"})
            def execute(args, cwd=None):
                return "tools/unrelated.py" if args[:3] == ["git", "diff", "--name-only"] else ""
            with patch.object(publisher, "command", side_effect=execute), self.assertRaisesRegex(RuntimeError, "outside"):
                publisher.submit(root, "deliverables")

    def test_corrupt_previous_snapshot_still_records_failure_without_overwrite(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = snap.data_dir(root) / snap.NAMES["deliverables"]
            snap.atomic_json(path, ["not a snapshot"])
            with redirect_stdout(io.StringIO()):
                report = refresh.refresh("deliverables", root=root, log=root / "result.json", cli_bin="none", identity="bot")
            self.assertEqual(report["status"], "failed")
            self.assertEqual(json.loads(path.read_text()), ["not a snapshot"])


class RealGitHandoffTests(unittest.TestCase):
    def test_retry_reuses_branch_and_recovers_unmerged_failure_state(self):
        from tools import workspace_refresh_publish as publisher
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote, seed, root = base / "remote.git", base / "seed", base / "run"
            original_command = publisher.command
            original_command(["git", "init", "--bare", "--initial-branch=main", str(remote)])
            original_command(["git", "clone", str(remote), str(seed)])
            original_command(["git", "config", "user.name", "Test"], cwd=seed)
            original_command(["git", "config", "user.email", "test@example.invalid"], cwd=seed)
            (seed / "README.md").write_text("Test repository")
            original_command(["git", "add", "README.md"], cwd=seed)
            original_command(["git", "commit", "-m", "test: initial"], cwd=seed)
            original_command(["git", "push", "origin", "main"], cwd=seed)
            status = snap.data_dir(root) / "deliverables-status.json"
            snap.atomic_json(status, {"status": "failed", "stage": "source-read", "failure_key": "one"})
            prs = []
            def execute(args, cwd=None):
                args = list(args)
                if args[0] == "gh":
                    if args[2] == "list":
                        return json.dumps(prs)
                    prs.append({"url": "https://github.com/example/repo/pull/1"})
                    return prs[0]["url"]
                if "clone" in args:
                    args[-2] = str(remote)
                return original_command(args, cwd=cwd)
            def head():
                return original_command(["git", "rev-parse", "refs/heads/chore/workspace-deliverables"], cwd=remote)
            with patch.object(publisher, "command", side_effect=execute):
                self.assertTrue(publisher.submit(root, "deliverables").endswith("/1"))
                first = head()
                publisher.submit(root, "deliverables")
                self.assertEqual(first, head())
                snap.atomic_json(status, {"status": "unchanged", "stage": "snapshot-validated", "content_sha256": "a"})
                publisher.submit(root, "deliverables")
                recovered = head()
                self.assertNotEqual(first, recovered)
                publisher.submit(root, "deliverables")
                self.assertEqual(recovered, head())
            self.assertEqual(len(prs), 1)
            self.assertEqual(original_command(["git", "rev-parse", "main"], cwd=seed),
                             original_command(["git", "rev-parse", "main"], cwd=remote))


class QueueBatchTests(unittest.TestCase):
    def test_multi_group_delivery_emits_one_deduplicated_request_and_dry_run_emits_none(self):
        import inspect
        from tools.build_queue.orchestration import process_build_queue
        from tools.build_queue.group_processing import QueueGroupProcessingResult
        kwargs = {name: Mock() for name in inspect.signature(process_build_queue).parameters}
        kwargs.update(cfg={}, config_path=Path('config.yaml'), data_root=None, dry_run=False,
                      immediate_only=False, workflow_action='publish', doc_phase=None, record_id=None,
                      record_ids=(), stderr=io.StringIO())
        kwargs['bootstrap_queue_session'].return_value = SimpleNamespace(
            source=Mock(), binding=Mock(), normalized_cli_action='publish', cli_bin='lark-cli', identity='bot')
        kwargs['load_pending_queue_state'].return_value = SimpleNamespace(
            pending_groups=[['r1'], ['r2']], can_write_started_at=True, can_write_force_phase2_refresh=True,
            can_write_data_sync=True, can_write_document_link_dd=True, can_write_feishu_cloud_doc=True,
            has_upload_dingtalk_field=True)
        kwargs['process_queue_record_group'].side_effect = [
            QueueGroupProcessingResult(1, workspace_deliveries=('r1',)),
            QueueGroupProcessingResult(1, workspace_deliveries=('r1', 'r2'))]
        with patch('tools.workspace_refresh_trigger.request_refresh') as request:
            self.assertEqual(process_build_queue(**kwargs), 0)
            request.assert_called_once_with('deliverables', ['r1', 'r1', 'r2'])
        kwargs['dry_run'] = True
        with patch('tools.workspace_refresh_trigger.request_refresh') as request:
            self.assertEqual(process_build_queue(**kwargs), 0)
            request.assert_not_called()

    def test_rtd_failure_never_records_workbench_updated(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            args = ['verify', '--root', tmp, '--revision', 'a' * 40, '--output', str(output)]
            response = {'results': [{'commit': 'a' * 40, 'state': {'code': 'finished'}, 'success': False}]}
            with patch('sys.argv', args), patch.object(verify, 'command', return_value='a' * 40), \
                    patch.object(verify, 'FetchSession') as session, patch.object(verify, 'verify_once') as online, \
                    redirect_stdout(io.StringIO()):
                session.return_value.fetch.return_value = json.dumps(response).encode()
                self.assertEqual(verify.main(), 1)
                online.assert_not_called()
            result = json.loads(output.read_text())
            self.assertEqual((result['stage'], result['status']), ('rtd-build', 'failed'))

    def test_rtd_api_uses_safe_query_free_transport_url(self):
        from tools.rtd_deployment_receipt import _canonical_probe_url
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            args = ['verify', '--root', tmp, '--revision', 'a' * 40, '--output', str(output)]
            response = {'results': [{'id': 42, 'commit': 'a' * 40,
                        'state': {'code': 'finished'}, 'success': True}]}

            def fetch(url):
                # Use the real transport URL gate; mocking FetchSession hid this failure.
                self.assertEqual(_canonical_probe_url(url), url)
                self.assertEqual(url, 'https://readthedocs.org/api/v3/projects/ht-doc/builds/')
                return json.dumps(response).encode()

            with patch('sys.argv', args), patch.object(verify, 'command', return_value='a' * 40), \
                    patch('tools.rtd_deployment_receipt._fetch', side_effect=fetch), \
                    patch.object(verify, 'verify_once', return_value={'status': 'verified'}), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main(), 0)
            self.assertEqual(json.loads(output.read_text())['rtd_build'], 42)
