from __future__ import annotations

import io
import logging
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from tools.utils import log


class ConsoleLogTest(unittest.TestCase):
    def setUp(self) -> None:
        log.configure(logging.INFO)

    def tearDown(self) -> None:
        log.configure(logging.INFO)

    def test_info_is_written_verbatim_to_the_current_stdout(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            log.get_logger("unit").info("[unit] 100% done {braces} kept")
        self.assertEqual("[unit] 100% done {braces} kept\n", out.getvalue())

    def test_stderr_logger_keeps_the_stream_of_print_file_stderr(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            log.get_logger("unit", stream="stderr").error("[unit] FAILURE x")
        self.assertEqual("", out.getvalue())
        self.assertEqual("[unit] FAILURE x\n", err.getvalue())

    def test_output_matches_print_byte_for_byte(self) -> None:
        message = "[unit] line with ünïcode and trailing space "
        printed, logged = io.StringIO(), io.StringIO()
        with redirect_stdout(printed):
            print(message)
        with redirect_stdout(logged):
            log.get_logger("unit").info(message)
        self.assertEqual(printed.getvalue(), logged.getvalue())

    def test_level_filters_lines(self) -> None:
        log.configure("WARNING")
        out = io.StringIO()
        with redirect_stdout(out):
            logger = log.get_logger("unit")
            logger.info("[unit] hidden")
            logger.warning("[unit] WARNING shown")
        self.assertEqual("[unit] WARNING shown\n", out.getvalue())

    def test_environment_variable_sets_the_level(self) -> None:
        with mock.patch.dict(os.environ, {log.LEVEL_ENV: "error"}):
            self.assertEqual(logging.ERROR, log.configure())
        with mock.patch.dict(os.environ, {log.LEVEL_ENV: ""}):
            self.assertEqual(logging.INFO, log.configure())

    def test_unknown_level_keeps_info_and_says_so(self) -> None:
        err = io.StringIO()
        with mock.patch.dict(os.environ, {log.LEVEL_ENV: "LOUD"}), redirect_stderr(err):
            self.assertEqual(logging.INFO, log.configure())
        self.assertIn("ignoring unknown AUTO_MANUAL_LOG_LEVEL='LOUD'", err.getvalue())

    def test_repeated_setup_never_duplicates_lines(self) -> None:
        log.configure()
        log.configure()
        out = io.StringIO()
        with redirect_stdout(out):
            log.get_logger("unit").info("once")
            log.get_logger("unit").info("twice")
        self.assertEqual("once\ntwice\n", out.getvalue())

    def test_records_do_not_reach_the_root_logger(self) -> None:
        seen: list[logging.LogRecord] = []

        class Recorder(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                seen.append(record)

        recorder = Recorder()
        logging.getLogger().addHandler(recorder)
        self.addCleanup(logging.getLogger().removeHandler, recorder)
        with redirect_stdout(io.StringIO()):
            log.get_logger("unit").info("[unit] private")
        self.assertEqual([], seen)

    def test_unknown_stream_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            log.get_logger("unit", stream="stdlog")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
