#!/usr/bin/env python3
"""Serve the list page plus a tiny shared-state API, so every phone on the link sees the same marks.

Usage: server.py <dir> [port=8765]
GET /state -> {"v": version, "st": {item_id: 1 bought | 2 missing}}
POST /state {"id": item_id, "v": 0|1|2} | {"reset": true} | {"seed": {...}} (seed applies only to an empty state)
"""
import json, os, sys, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

root = os.path.abspath(sys.argv[1])
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
state_file = os.path.join(root, "state.json")
lock = threading.Lock()
state = {"v": 0, "st": {}}
if os.path.exists(state_file):
    try:
        state = json.load(open(state_file, encoding="utf-8"))
    except ValueError:
        pass


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=root, **k)

    def log_message(self, *a):
        pass

    def send_state(self):
        body = json.dumps(state, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/state":
            with lock:
                return self.send_state()
        if path not in ("/", "/index.html"):
            return self.send_error(404)
        self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/state":
            return self.send_error(404)
        n = int(self.headers.get("Content-Length") or 0)
        if n > 100_000:
            return self.send_error(413)
        try:
            body = json.loads(self.rfile.read(n))
        except ValueError:
            return self.send_error(400)
        with lock:
            st = state["st"]
            if body.get("reset"):
                st.clear()
            elif isinstance(body.get("seed"), dict):
                if st:
                    return self.send_state()
                st.update({k: v for k, v in body["seed"].items() if isinstance(k, str) and v in (1, 2)})
            elif isinstance(body.get("id"), str) and body.get("v") in (0, 1, 2):
                if body["v"]:
                    st[body["id"]] = body["v"]
                else:
                    st.pop(body["id"], None)
            else:
                return self.send_error(400)
            state["v"] += 1
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
            self.send_state()


ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
