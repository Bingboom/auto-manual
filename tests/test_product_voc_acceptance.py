from __future__ import annotations

import json
import threading
import unittest
import uuid
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from integrations.product_voc.intake import Intake
from integrations.product_voc.server import make_handler


def submission() -> dict[str, str]:
    return {
        "request_id": str(uuid.uuid4()),
        "suggestion": "TEST: improve the handle.",
        "model": "JE-TEST",
        "use_case": "TEST only",
        "context": "Page: JE-TEST/EU/en/md/manual.html",
        "website": "",
    }


class ProductVocAcceptanceTests(unittest.TestCase):
    def test_http_submission_is_verified_and_idempotent_after_restart(self):
        with TemporaryDirectory() as directory, patch("integrations.product_voc.intake.time.sleep"):
            state = Path(directory) / "voc.sqlite"
            writer = Mock()
            writer.create.return_value = "recTEST"
            body = submission()

            server = self.start_server(Intake(state, writer))
            try:
                self.assertEqual((200, True), self.post(server, body))
                self.assertEqual((200, True), self.post(server, body))
            finally:
                server.shutdown()
                server.server_close()
                server.intake.db.close()

            restarted = self.start_server(Intake(state, writer))
            try:
                self.assertEqual((200, True), self.post(restarted, body))
            finally:
                restarted.shutdown()
                restarted.server_close()
                restarted.intake.db.close()

            writer.create.assert_called_once()
            writer.verify.assert_called_once()

    @staticmethod
    def start_server(intake: Intake) -> ThreadingHTTPServer:
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(intake, {"https://ht-doc.readthedocs.io"}),
        )
        server.intake = intake
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server

    @staticmethod
    def post(server: ThreadingHTTPServer, body: dict[str, str]) -> tuple[int, bool]:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request(
                "POST",
                "/api/voc",
                body=json.dumps(body),
                headers={
                    "Origin": "https://ht-doc.readthedocs.io",
                    "Content-Type": "application/json",
                },
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read())["ok"]
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
