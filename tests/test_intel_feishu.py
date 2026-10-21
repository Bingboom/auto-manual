"""lark-cli calls name no argument when they fail, and a table is read completely or not at all."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tools.intel import feishu

TOKEN = "bascnSECRETTOKEN"


def done(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class Recorder:
    def __init__(self, *results):
        self.results, self.calls, self.slept = list(results), [], []

    def execute(self, call, **options):
        self.calls.append((call, options))
        return self.results.pop(0)

    def run(self, identity="bot"):
        return feishu.runner(sys.executable, identity, execute=self.execute, sleep=self.slept.append)


class CommandTests(unittest.TestCase):
    def test_command_splits_like_a_shell_and_resolves_the_program(self):
        self.assertEqual(feishu.command(f"{sys.executable} --profile 'prod team'"),
                         [sys.executable, "--profile", "prod team"])
        self.assertEqual(feishu.command("no-such-program-xyz -v"), ["no-such-program-xyz", "-v"])
        self.assertEqual(Path(feishu.command(Path(sys.executable).name)[0]).name, Path(sys.executable).name)
        with self.assertRaises(ValueError):
            feishu.command("  ")

    def test_payload_is_the_printed_json_object(self):
        self.assertEqual(feishu.payload_of('{"code": 0}'), {"code": 0})
        self.assertEqual(feishu.payload_of('notice: update available\n{"code": 0, "data": {}}\n'),
                         {"code": 0, "data": {}})
        for text in ("", "plain text", "[1, 2]", "{broken"):
            with self.subTest(text=text):
                with self.assertRaises(feishu.LarkError):
                    feishu.payload_of(text)


class RunnerTests(unittest.TestCase):
    def test_identity_follows_the_subcommand_and_the_payload_is_returned(self):
        recorder = Recorder(done(stdout='{"code": 0, "data": {"message_id": "om_1"}}'))
        payload = recorder.run()(["im", "+messages-send", "--chat-id", "oc_1"])
        self.assertEqual(payload["data"]["message_id"], "om_1")
        call, options = recorder.calls[0]
        self.assertEqual(call, [sys.executable, "im", "+messages-send", "--as", "bot", "--chat-id", "oc_1"])
        self.assertEqual((options["check"], options["capture_output"], options["encoding"]), (False, True, "utf-8"))
        Recorder(done(stdout='{"code": 0}')).run(identity="")(["base", "+record-list"])

    def test_failures_name_the_status_or_code_never_the_arguments(self):
        # lark-cli 1.x exits 3 and prints {"ok": false, "error": {...}} to stderr.
        cli_error = json.dumps({"ok": False, "error": {"type": "api", "code": 91403, "message": f"no access {TOKEN}"}})
        for result, message in ((done(1, stderr=f"invalid token {TOKEN}"), "status 1"),
                                (done(3, stderr=f"[WARN] proxy detected\n{cli_error}"), "status 3, response code 91403"),
                                (done(stdout='{"code": 91403, "msg": "forbidden"}'), "code 91403"),
                                (done(stdout='{"ok": false, "error": {"code": 10014}}'), "code 10014"),
                                (done(stdout='{"ok": false}'), "code None"),
                                (done(stdout="not json"), "no JSON object")):
            with self.subTest(message=message):
                with self.assertRaises(feishu.LarkError) as raised:
                    Recorder(result).run()(["base", "+record-list", "--base-token", TOKEN])
                self.assertIn(message, str(raised.exception))
                self.assertNotIn(TOKEN, str(raised.exception))

    def test_a_failed_call_adds_only_a_numeric_response_code(self):
        for stderr, expected in (('{"ok": false, "error": {"code": 91403}}', ", response code 91403"),
                                 ('{"ok": false, "error": {"code": true}}', ""),
                                 ('{"ok": false, "error": {"code": "0"}}', ""),
                                 ('{"code": "x91403"}', ""),
                                 ("Error: broken pipe", "")):
            with self.subTest(stderr=stderr):
                with self.assertRaises(feishu.LarkError) as raised:
                    Recorder(done(3, stderr=stderr)).run()(["base", "+record-list"])
                self.assertEqual(str(raised.exception), "lark-cli exited with status 3" + expected)

    def test_rate_limits_are_retried_with_bounded_backoff(self):
        limited = done(stdout='{"code": 429, "retry_after": 5}')
        recorder = Recorder(limited, done(1, stderr="Too Many Requests"), done(stdout='{"code": 0}'))
        self.assertEqual(recorder.run()(["base", "+record-list"]), {"code": 0})
        self.assertEqual(recorder.slept, [5.0, 2.0])
        exhausted = Recorder(*[limited] * (feishu.RETRIES + 1))
        with self.assertRaises(feishu.LarkError):
            exhausted.run()(["base", "+record-list"])
        self.assertEqual(len(exhausted.slept), feishu.RETRIES)
        self.assertLessEqual(max(exhausted.slept), feishu.MAX_DELAY)


def pages(columns, rows, *, size=feishu.PAGE_SIZE, total="auto", rev=7):
    def run(args):
        offset = int(args[args.index("--offset") + 1])
        page = rows[offset:offset + size]
        data = {"fields": columns, "data": page, "record_id_list": [f"rec{offset + i}" for i in range(len(page))],
                "has_more": offset + len(page) < len(rows), "rev": rev}
        if total is not None:
            data["total"] = len(rows) if total == "auto" else total
        return {"code": 0, "data": data}
    return run


class CompleteRowsTests(unittest.TestCase):
    def test_every_page_is_read_in_order(self):
        rows = [[f"title {i}", i] for i in range(450)]
        columns, read = feishu.complete_rows(pages(["标题", "数"], rows), "b", "t")
        self.assertEqual(columns, ["标题", "数"])
        self.assertEqual([record for record, _ in read][:2] + [read[-1][0]], ["rec0", "rec1", "rec449"])
        self.assertEqual(read[449][1], {"标题": "title 449", "数": 449})

    def test_partial_or_inconsistent_reads_raise(self):
        def changing(field):
            calls = []

            def run(args):
                calls.append(args)
                data = {"fields": ["a"] if field != "fields" or len(calls) == 1 else ["b"],
                        "data": [[1]] * (200 if len(calls) == 1 else 1),
                        "record_id_list": [f"rec{len(calls)}-{i}" for i in range(200 if len(calls) == 1 else 1)],
                        "total": 201 if field != "total" or len(calls) == 1 else 300, "has_more": len(calls) == 1,
                        "rev": 1 if field != "rev" or len(calls) == 1 else 2}
                return {"code": 0, "data": data}
            return run
        cases = {
            "error code": lambda args: {"code": 1, "msg": "denied"},
            "no schema": lambda args: {"code": 0, "data": {"data": []}},
            "rows without ids": lambda args: {"code": 0, "data": {"fields": ["a"], "data": [[1]], "record_id_list": []}},
            "repeated id": lambda args: {"code": 0, "data": {"fields": ["a"], "data": [[1], [2]],
                                                             "record_id_list": ["rec1", "rec1"]}},
            "short total": pages(["a"], [[1], [2]], total=5),
            "more after a short page": lambda args: {"code": 0, "data": {"fields": ["a"], "data": [[1]],
                                                                         "record_id_list": ["rec1"], "has_more": True}},
            "schema change": changing("fields"), "total change": changing("total"), "revision change": changing("rev"),
        }
        for name, run in cases.items():
            with self.subTest(name):
                with self.assertRaises(feishu.LarkError):
                    feishu.complete_rows(run, "b", "t")

    def test_calls_ask_for_full_json_pages(self):
        calls = []

        def run(args):
            calls.append(args)
            return pages(["a"], [[1]])(args)
        feishu.complete_rows(run, "bascnB", "tblT")
        self.assertEqual(calls, [["base", "+record-list", "--base-token", "bascnB", "--table-id", "tblT",
                                  "--format", "json", "--limit", "200", "--offset", "0"]])
        self.assertEqual(json.loads(json.dumps(calls)), calls)


if __name__ == "__main__":
    unittest.main()
