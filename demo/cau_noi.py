# -*- coding: utf-8 -*-
"""Cau noi giua trang web va Ollama.

Chrome chan mot trang https (vi du tren Vercel) goi vao localhost, tru khi may chu
tra ve header Access-Control-Allow-Private-Network. Ollama khong tra header do, nen
chay file nay lam trung gian:

    python cau_noi.py

Roi trong trang demo, o o "Dia chi Ollama" doi thanh  http://localhost:11435
"""
import http.server
import json
import socketserver
import sys
import urllib.error
import urllib.request

CONG = 11435
OLLAMA = "http://localhost:11434"


class CauNoi(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self):
        o = self.headers.get("Origin", "*")
        self.send_header("Access-Control-Allow-Origin", o)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # header then chot: cho phep trang cong khai goi vao may noi bo
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _chuyen(self, than=None):
        url = OLLAMA + self.path
        req = urllib.request.Request(url, data=than, method=self.command)
        if than is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = r.read()
                ma = r.status
        except urllib.error.HTTPError as e:
            data, ma = e.read(), e.code
        except Exception as e:
            data = json.dumps({"error": str(e)}).encode()
            ma = 502
        self.send_response(ma)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._chuyen()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self._chuyen(self.rfile.read(n))

    def log_message(self, fmt, *a):
        sys.stdout.write("  %s\n" % (fmt % a))


class May(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Cau noi dang chay tai  http://localhost:%d" % CONG)
    print("Trong trang demo, doi o 'Dia chi Ollama' thanh dia chi tren.")
    print("Nhan Ctrl+C de dung.")
    with May(("127.0.0.1", CONG), CauNoi) as m:
        m.serve_forever()
