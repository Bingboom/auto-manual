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
from tools.rtd.deliverables import snapshot_problems
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
            self.assertEqual(rows[0]["state"], "待复核")
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
            html = (b'<span data-workspace-source="deliverables" data-snapshot-sha256=""></span>'
                    b'<span data-workspace-source="corpus" data-snapshot-sha256=""></span>'
                    b'<span data-workspace-source="web_progress" data-snapshot-sha256=""></span>')
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

    def test_a_sign_in_redirect_reads_as_login_required(self):
        from tools.rtd.deployment_receipt import CrossOriginRedirect

        def login(_url):
            raise CrossOriginRedirect("https://app.readthedocs.com/cas/login?service=x")

        def elsewhere(_url):
            raise CrossOriginRedirect("https://example.com/moved")

        with TemporaryDirectory() as tmp, patch.object(verify, "command", return_value=""):
            with self.assertRaises(verify.LoginRequired):
                verify.verify_once(Path(tmp), "target", fetch=login)
            with self.assertRaises(CrossOriginRedirect) as other:
                verify.verify_once(Path(tmp), "target", fetch=elsewhere)
            self.assertNotIsInstance(other.exception, verify.LoginRequired)


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

    def test_web_progress_reads_the_bound_tables_and_history(self):
        from tools.rtd import web_progress as wp
        from tools.rtd import web_reviews as wr
        site = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"
        grids = {
            "web": {"data": {"fields": ["型号", wp.LINK_FIELD, wp.CHECK_FIELD, wp.SKU_FIELD], "record_id_list": ["recW1"],
                             "data": [["JE-A", {"link": f"{site}/JE-A/EU/en/md/manual.html"}, True, [{"text": "HTE1-EU-JAK"}]]],
                             "total": 1, "has_more": False}},
            "review": {"data": {"fields": list(wr.FIELDS.values()), "record_id_list": ["recR1"],
                                "data": [["JE-B", "B", "美规", "en", "v0.1", "2026-10-20", "审核中", "2",
                                          {"link": "https://review.example/JE-B/US/index.html"}, None]],
                                "total": 1, "has_more": False}},
        }

        def run(args):
            return grids[args[args.index("--table-id") + 1]]
        timeline = [{"date": "2026-10-01", "added": 1, "langs": 1, "editions": 1, "models": 1}]
        env = {"FEISHU_PUBLISHED_DOCS_BASE_TOKEN": "base", "FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID": "web",
               "FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID": "review", "FEISHU_PUBLISHED_DOCS_URL": "https://t.feishu.cn/wiki/n"}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "tools" / "rtd_portal_assets"
            assets.mkdir(parents=True)
            (assets / "workspace_refresh_sources.json").write_text(json.dumps(
                {"web_progress": snap.digest(["base", "web"]), "web_progress_reviews": snap.digest(["base", "review"])}))
            with patch.dict(os.environ, env), redirect_stdout(io.StringIO()):
                result = refresh.refresh("web_progress", root=root, log=root / "result.json", cli_bin="unused",
                                         identity="bot", run=run, history=lambda _: timeline)
            self.assertEqual(result["status"], "changed")
            # The snapshot's source stays the 网页文档 binding, so earlier snapshots still match.
            self.assertEqual(result["source"], {"identity_sha256": snap.digest(["base", "web"])})
            saved = json.loads((snap.data_dir(root) / snap.NAMES["web_progress"]).read_text())
            self.assertEqual((saved["checked"], saved["sold"], saved["timeline"]), (["JE-A/EU/en"], {"JE-A": ["EU"]}, timeline))
            self.assertEqual([(r["model"], r["market"], r["open"]) for r in saved["reviews"]], [("JE-B", "US", 2)])
            self.assertEqual((saved["records"], saved["feishu"]["reviews"]),
                             ({"JE-A/EU/en": "recW1"}, "https://t.feishu.cn/wiki/n?table=review"))
            # A table the binding does not name, or a missing review table or address, is refused before any read.
            for change in ({"FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID": "other"}, {"FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID": "other"},
                           {"FEISHU_PUBLISHED_DOCS_REVIEW_TABLE_ID": ""}, {"FEISHU_PUBLISHED_DOCS_URL": "t.feishu.cn"}):
                with self.subTest(change), patch.dict(os.environ, dict(env, **change)), redirect_stdout(io.StringIO()):
                    failed = refresh.refresh("web_progress", root=root, log=root / "result.json", cli_bin="unused",
                                             identity="bot", run=Mock(side_effect=AssertionError("read")),
                                             history=lambda _: timeline)
                self.assertEqual(failed["status"], "failed")

    def test_corpus_revision_changes_hash_without_changing_counts(self):
        from tools.rtd.system_workspace import corpus_export
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
                if args[:2] == ["git", "ls-remote"]:
                    return "0" * 40 + "\trefs/heads/chore/workspace-deliverables"
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
    @staticmethod
    def seed_remote(base: Path, original_command) -> tuple[Path, Path]:
        remote, seed = base / "remote.git", base / "seed"
        original_command(["git", "init", "--bare", "--initial-branch=main", str(remote)])
        original_command(["git", "clone", str(remote), str(seed)])
        original_command(["git", "config", "user.name", "Test"], cwd=seed)
        original_command(["git", "config", "user.email", "test@example.invalid"], cwd=seed)
        (seed / "README.md").write_text("Test repository")
        original_command(["git", "add", "README.md"], cwd=seed)
        original_command(["git", "commit", "-m", "test: initial"], cwd=seed)
        original_command(["git", "push", "origin", "main"], cwd=seed)
        return remote, seed

    def test_retry_reuses_branch_and_recovers_unmerged_failure_state(self):
        from tools import workspace_refresh_publish as publisher
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "run"
            original_command = publisher.command
            remote, seed = self.seed_remote(base, original_command)
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

    def test_branch_left_by_a_merged_pr_restarts_from_main(self):
        # Hello-Docs #242: the leftover branch of the squash-merged #240 made the next content PR conflict.
        from tools import workspace_refresh_publish as publisher
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "run"
            original_command = publisher.command
            remote, seed = self.seed_remote(base, original_command)
            status = snap.data_dir(root) / "deliverables-status.json"
            relative = status.relative_to(root).as_posix()
            branch = "refs/heads/chore/workspace-deliverables"
            prs = []
            def execute(args, cwd=None):
                args = list(args)
                if args[0] == "gh":
                    if args[2] == "list":
                        return json.dumps(prs)
                    prs.append({"url": f"https://github.com/example/repo/pull/{len(prs) + 1}"})
                    return prs[-1]["url"]
                if "clone" in args:
                    args[-2] = str(remote)
                return original_command(args, cwd=cwd)
            def git(*args):
                return original_command(["git", *args], cwd=remote)
            snap.atomic_json(status, {"status": "failed", "stage": "source-read", "failure_key": "one"})
            with patch.object(publisher, "command", side_effect=execute):
                self.assertTrue(publisher.submit(root, "deliverables").endswith("/1"))
            # Squash-merge the PR: main gains the file in a commit of its own, the branch stays behind.
            (seed / relative).parent.mkdir(parents=True, exist_ok=True)
            (seed / relative).write_text(git("show", f"{branch}:{relative}") + "\n")
            original_command(["git", "add", relative], cwd=seed)
            original_command(["git", "commit", "-m", "chore(workspace): refresh deliverables data (#1)"], cwd=seed)
            original_command(["git", "push", "origin", "main"], cwd=seed)
            prs.clear()
            snap.atomic_json(status, {"status": "failed", "stage": "source-read", "failure_key": "two"})
            with patch.object(publisher, "command", side_effect=execute):
                self.assertTrue(publisher.submit(root, "deliverables").endswith("/1"))
            self.assertEqual(git("rev-parse", f"{branch}^"), git("rev-parse", "main"))
            self.assertEqual(git("diff", "--name-only", "main", branch), relative)
            self.assertIn('"two"', git("show", f"{branch}:{relative}"))


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
                    patch.dict(os.environ, {verify.API_TOKEN_ENV: 'token'}), \
                    patch.object(verify, 'fetch_builds', return_value=json.dumps(response).encode()), \
                    patch.object(verify, 'verify_once') as online, redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main(), 1)
                online.assert_not_called()
            result = json.loads(output.read_text())
            self.assertEqual((result['stage'], result['status']), ('rtd-build', 'failed'))

    def test_community_rtd_api_uses_safe_query_free_transport_url(self):
        from tools.rtd.deployment_receipt import _canonical_probe_url
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
                    patch.object(verify, 'BASE_URL', 'https://ht-doc.readthedocs.io/'), \
                    patch.dict(os.environ, {verify.API_TOKEN_ENV: 'business-only'}), \
                    patch('tools.rtd.deployment_receipt._fetch', side_effect=fetch), \
                    patch.object(verify, 'verify_once', return_value={'status': 'verified'}), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main(), 0)
            result = json.loads(output.read_text())
            self.assertEqual(result['rtd_build'], 42)
            self.assertEqual(result['rtd_url'], 'https://app.readthedocs.org/projects/ht-doc/builds/42/')

    def test_business_rtd_api_sends_the_token_only_to_its_builds_endpoint(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            args = ['verify', '--root', tmp, '--revision', 'a' * 40, '--output', str(output)]
            response = {'results': [{'id': 7, 'commit': 'a' * 40, 'state': {'code': 'finished'}, 'success': True}]}
            seen = []

            def urlopen(request, timeout):
                seen.append((request.full_url, request.get_header('Authorization')))
                return io.BytesIO(json.dumps(response).encode())

            with patch('sys.argv', args), patch.object(verify, 'command', return_value='a' * 40), \
                    patch.dict(os.environ, {verify.API_TOKEN_ENV: 'secret'}), \
                    patch.object(verify, 'urlopen', side_effect=urlopen), \
                    patch.object(verify, 'verify_once', return_value={'status': 'verified'}), \
                    redirect_stdout(io.StringIO()) as out:
                self.assertEqual(verify.main(), 0)
            self.assertEqual(seen, [('https://readthedocs.com/api/v3/projects/ht-docs-ht-manuals/builds/', 'Token secret')])
            result = json.loads(output.read_text())
            self.assertEqual(result['rtd_url'], 'https://app.readthedocs.com/projects/ht-docs-ht-manuals/builds/7/')
            self.assertNotIn('secret', out.getvalue() + output.read_text())

    def test_a_sign_in_only_site_is_verified_by_this_revisions_build(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            args = ['verify', '--root', tmp, '--revision', 'a' * 40, '--attempts', '20', '--output', str(output)]
            response = {'results': [{'id': 9, 'commit': 'a' * 40, 'state': {'code': 'finished'}, 'success': True}]}
            with patch('sys.argv', args), patch.object(verify, 'command', return_value='a' * 40), \
                    patch.dict(os.environ, {verify.API_TOKEN_ENV: 'token'}), \
                    patch.object(verify, 'fetch_builds', return_value=json.dumps(response).encode()), \
                    patch.object(verify.time, 'sleep') as sleep, \
                    patch.object(verify, 'verify_once', side_effect=verify.LoginRequired('online-login-required')), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main(), 0)
            sleep.assert_not_called()
            result = json.loads(output.read_text())
            self.assertEqual((result['status'], result['stage'], result['rtd_build']), ('verified', 'rtd-build-verified', 9))
            self.assertEqual(result['online'], 'Not checked (site requires sign-in)')
            self.assertIn('deliverables', result['sources'])

    def test_a_sign_in_only_site_without_a_token_fails_at_once(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            args = ['verify', '--root', tmp, '--revision', 'a' * 40, '--attempts', '20', '--output', str(output)]
            with patch('sys.argv', args), patch.object(verify, 'command', return_value='a' * 40), \
                    patch.dict(os.environ, {verify.API_TOKEN_ENV: ''}), patch.object(verify.time, 'sleep') as sleep, \
                    patch.object(verify, 'verify_once', side_effect=verify.LoginRequired('online-login-required')) as online, \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main(), 1)
            self.assertEqual((online.call_count, sleep.call_count), (1, 0))
            result = json.loads(output.read_text())
            self.assertEqual((result['status'], result['stage']), ('failed', 'online-verification'))
            self.assertIn(verify.API_TOKEN_ENV, result['online'])

    def test_without_a_business_token_only_this_revisions_receipt_decides(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            args = ['verify', '--root', tmp, '--revision', 'a' * 40, '--attempts', '2', '--output', str(output)]
            results = [ValueError('online-version-mismatch'), {'status': 'verified', 'stage': 'online-verified'}]
            with patch('sys.argv', args), patch.object(verify, 'command', return_value='a' * 40), \
                    patch.dict(os.environ, {verify.API_TOKEN_ENV: ''}), \
                    patch.object(verify, 'fetch_builds') as builds, patch.object(verify.time, 'sleep'), \
                    patch.object(verify, 'verify_once', side_effect=results) as online, \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(verify.main(), 0)
            builds.assert_not_called()
            self.assertEqual(online.call_count, 2)
            result = json.loads(output.read_text())
            self.assertEqual(result['rtd_build'], f'Not checked (no {verify.API_TOKEN_ENV})')
            self.assertEqual(result['status'], 'verified')
