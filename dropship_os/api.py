from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlparse
from .db import Database


def make_handler(db: Database):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, payload: dict | list):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/health": return self._json(200, {"status": "PASS"})
            if path == "/work-orders":
                with db.connect() as conn: rows = [dict(row) for row in conn.execute("SELECT * FROM work_orders ORDER BY created_at DESC LIMIT 100")]
                return self._json(200, rows)
            if path == "/incidents":
                with db.connect() as conn: rows = [dict(row) for row in conn.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 100")]
                return self._json(200, rows)
            return self._json(404, {"error": "not found"})
        def log_message(self, format, *args): return
    return Handler


def serve(db: Database, host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(db)); print(json.dumps({"status": "RUNNING", "host": host, "port": port})); server.serve_forever()
