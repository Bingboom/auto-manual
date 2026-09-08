"""Local-only preview for Safari: no upload and no browser security changes."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser


def main():
    root = Path(__file__).resolve().parent
    # Bind loopback and let the OS select a free port; never expose a LAN server.
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"手册已在本机打开：{url}\n无需上传。阅读期间请保留此窗口，关闭窗口即可结束预览。", flush=True)
        webbrowser.open(url)
        try:
            thread.join()
        except KeyboardInterrupt:
            server.shutdown()


if __name__ == "__main__":
    main()
