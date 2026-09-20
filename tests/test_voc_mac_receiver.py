import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from integrations.product_voc import server as voc_server
from scripts import voc_mac_receiver


class VocMacReceiverTests(unittest.TestCase):
    def test_start_requires_explicit_profile(self):
        with self.assertRaises(SystemExit):
            voc_mac_receiver.parser().parse_args([
                "start", "--base", "base", "--table", "table", "--origin", "https://example.com"
            ])

    def test_child_command_preserves_explicit_profile_and_origins(self):
        args = argparse.Namespace(
            profile="cli_verified", base="base", table="table",
            runtime_dir=Path("/tmp/private-voc"), port=9198,
            origin=["https://example.com", "http://127.0.0.1:9198"],
            preview=True, cloudflare_tunnel=False,
        )
        command = voc_mac_receiver.child_command(args)
        self.assertEqual(command[command.index("--profile") + 1], "cli_verified")
        self.assertEqual([command[index + 1] for index, item in enumerate(command) if item == "--origin"], args.origin)
        self.assertIn("--preview", command)
        self.assertNotIn("--cloudflare-tunnel", command)

    def test_private_runtime_tightens_existing_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime"
            path.mkdir(mode=0o755)
            result = voc_mac_receiver.private_runtime(path)
            self.assertEqual(result, path.resolve())
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o700)

    def test_origin_must_be_bare_https_or_loopback(self):
        voc_mac_receiver.validate_origins([
            "https://ht-doc.readthedocs.io", "http://127.0.0.1:9198"
        ])
        with self.assertRaises(ValueError):
            voc_mac_receiver.validate_origins(["https://example.com/path"])

    @patch("scripts.voc_mac_receiver.make_handler", return_value=object())
    @patch("scripts.voc_mac_receiver.signal.signal")
    @patch("scripts.voc_mac_receiver.LimitedServer")
    @patch("scripts.voc_mac_receiver.Intake")
    @patch("scripts.voc_mac_receiver.BotWriter")
    def test_run_uses_profile_and_loopback_only(
        self, writer_type, intake_type, server_type, _signal, _handler
    ):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(
                profile="cli_verified", base="base", table="table", runtime_dir=Path(directory),
                port=9198, origin=["https://example.com"], preview=False, cloudflare_tunnel=False,
            )
            intake_type.return_value.db = MagicMock()
            self.assertEqual(voc_mac_receiver.run_receiver(args), 0)
            writer_type.assert_called_once_with(base="base", table="table", profile="cli_verified")
            writer_type.return_value.preflight.assert_called_once_with()
            self.assertEqual(server_type.call_args.args[0], ("127.0.0.1", 9198))

    @patch("scripts.voc_mac_receiver.BotWriter")
    def test_failed_preflight_leaves_no_pid_file(self, writer_type):
        writer_type.return_value.preflight.side_effect = RuntimeError("preflight failed")
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            args = argparse.Namespace(
                profile="cli_verified", base="base", table="table", runtime_dir=runtime,
                port=9198, origin=["https://example.com"], preview=False,
                cloudflare_tunnel=False,
            )
            with self.assertRaisesRegex(RuntimeError, "preflight failed"):
                voc_mac_receiver.run_receiver(args)
            self.assertFalse((runtime / "receiver.pid").exists())

    @patch("scripts.voc_mac_receiver.owns_process", return_value=False)
    @patch("scripts.voc_mac_receiver.is_running", return_value=True)
    @patch("scripts.voc_mac_receiver.read_pid", return_value=123)
    def test_stop_refuses_unrecognized_pid(self, _read, _running, _owns):
        args = argparse.Namespace(runtime_dir=Path("/tmp/private-voc"), stop_timeout=0.0)
        with patch("scripts.voc_mac_receiver.os.kill") as kill:
            self.assertEqual(voc_mac_receiver.stop_receiver(args), 2)
            kill.assert_not_called()

    @patch("scripts.voc_mac_receiver.subprocess.Popen")
    @patch("scripts.voc_mac_receiver.owns_process", return_value=False)
    @patch("scripts.voc_mac_receiver.is_running", return_value=True)
    def test_start_ignores_stale_pid_reused_by_other_process(self, _running, _owns, popen):
        popen.return_value.poll.return_value = 1
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "receiver.pid").write_text('{"pid": 123}\n', encoding="utf-8")
            args = argparse.Namespace(
                profile="cli_verified", base="base", table="table", runtime_dir=runtime,
                port=9198, origin=["https://example.com"], preview=False,
                cloudflare_tunnel=False, start_timeout=0.0,
            )
            self.assertEqual(voc_mac_receiver.start_receiver(args), 1)
            popen.assert_called_once()

    @patch("integrations.product_voc.server.LimitedServer")
    @patch("integrations.product_voc.server.Intake")
    @patch("integrations.product_voc.server.BotWriter")
    def test_server_entrypoint_passes_explicit_profile(self, writer_type, _intake_type, _server_type):
        argv = [
            "server", "--profile", "cli_verified", "--base", "base", "--table", "tblTable",
            "--state", "/tmp/receipts.sqlite", "--origin", "https://example.com",
        ]
        with patch("sys.argv", argv):
            voc_server.main()
        writer_type.assert_called_once_with(base="base", table="tblTable", profile="cli_verified")


if __name__ == "__main__":
    unittest.main()
