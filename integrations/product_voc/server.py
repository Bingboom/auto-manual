"""Loopback-only Mac agent receiver; expose only through a dedicated HTTPS ingress."""
from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from integrations.product_voc.intake import BotWriter, Intake, IntakeError
from tools.rtd_portal import ASSETS
from tools.rtd_product_voc import suggestion_markup
from tools.utils.path_utils import PathSegments

MAX_BODY = 24000


class LimitedServer(ThreadingHTTPServer):
    """Bound concurrent sockets as well as downstream writes."""
    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


def make_handler(intake: Intake, origins: set[str], preview: bool = False, cloudflare_tunnel: bool = False):
    class Handler(BaseHTTPRequestHandler):
        server_version = "VOC"

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_args):
            pass  # Do not log visitor addresses, raw forms or URL queries.

        def send(self, status: int, body: bytes, content_type: str = "application/json"):
            self.send_response(status)
            origin = self.headers.get("Origin", "")
            if origin in origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            if status == 429:
                self.send_header("Retry-After", "600")
            if self.command == "OPTIONS" and status == 204:
                self.send_header("Access-Control-Allow-Methods", "POST")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            allowed = (self.path == "/api/voc" and self.headers.get("Origin") in origins
                       and self.headers.get("Access-Control-Request-Method") == "POST"
                       and self.headers.get("Access-Control-Request-Headers", "").lower() == "content-type")
            self.send(204 if allowed else 403, b"")

        def do_POST(self):
            try:
                if self.path != "/api/voc":
                    raise IntakeError(404, "not_found")
                if self.headers.get("Origin") not in origins:
                    raise IntakeError(403, "origin_denied")
                if (self.headers.get("Content-Type", "").split(";")[0] != "application/json"
                        or self.headers.get("Transfer-Encoding")):
                    raise IntakeError(400, "json_required")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    raise IntakeError(413, "body_too_large")
                body = self.rfile.read(length)
                if len(body) != length:
                    raise IntakeError(400, "incomplete_body")
                # A dedicated Cloudflare Tunnel overwrites this header. Without that
                # header, conservatively rate-limit all direct clients by socket peer.
                peer = (self.headers.get("CF-Connecting-IP") if cloudflare_tunnel else None) or self.client_address[0]
                result = intake.submit(json.loads(body), peer)
                self.send(200, json.dumps(result).encode())
            except IntakeError as exc:
                self.send(exc.status, json.dumps({"ok": False, "error": exc.code}).encode())
            except (ValueError, UnicodeError):
                self.send(400, b'{"ok":false,"error":"invalid_json"}')
            except Exception:
                self.send(503, b'{"ok":false,"error":"unavailable"}')

        def do_GET(self):
            if self.path == "/healthz":
                self.send(200, b'{"ok":true}')
            elif preview and self.path == "/preview":
                markup = suggestion_markup(endpoint="/api/voc", context="TEST: Mac VOC integration preview")
                html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                        '<meta name="viewport" content="width=device-width,initial-scale=1">'
                        '<meta name="robots" content="noindex,nofollow"><title>VOC integration preview</title>'
                        '<link rel="stylesheet" href="/product-voc.css"><body><h1>Product suggestions · TEST preview</h1>'
                        + markup + '<script defer src="/product-voc.js"></script></body></html>')
                self.send(200, html.encode(), "text/html; charset=utf-8")
            elif preview and self.path in ("/product-voc.js", "/product-voc.css"):
                content_type = "text/javascript" if self.path.endswith(".js") else "text/css"
                self.send(200, (ASSETS / PathSegments.STATIC / self.path[1:]).read_bytes(), content_type)
            else:
                self.send(404, b'{"ok":false,"error":"not_found"}')
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--profile", default="prod", help="lark-cli profile containing the bot identity")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--port", type=int, default=9198)
    parser.add_argument("--origin", action="append", required=True)
    parser.add_argument("--preview", action="store_true", help="Serve a clearly marked integration-test form")
    parser.add_argument("--cloudflare-tunnel", action="store_true", help="Trust CF-Connecting-IP only behind a dedicated Cloudflare Tunnel")
    args = parser.parse_args()
    for origin in args.origin:
        url = urlsplit(origin)
        loopback = url.scheme == "http" and url.hostname in ("127.0.0.1", "localhost")
        if (not url.hostname or url.username or url.password or url.path or url.query or url.fragment
                or not (url.scheme == "https" or loopback)):
            parser.error("Origins must be bare HTTPS origins (HTTP loopback allowed for tests)")
    writer = BotWriter(base=args.base, table=args.table, profile=args.profile)
    writer.preflight()
    intake = Intake(args.state, writer)
    server = LimitedServer(("127.0.0.1", args.port), make_handler(
        intake, set(args.origin), args.preview, args.cloudflare_tunnel))
    print(f"VOC receiver listening on 127.0.0.1:{args.port}; fixed table {args.table}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
