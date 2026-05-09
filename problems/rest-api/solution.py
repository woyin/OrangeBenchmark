import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class TaskHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send_json(self, status: int, payload=None):
        self.send_response(status)
        if payload is None:
            self.end_headers()
            return
        body = json.dumps(payload).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode() if length else "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _task_id_from_path(self):
        parts = self.path.split("?", 1)[0].strip("/").split("/")
        if len(parts) != 2 or parts[0] != "tasks":
            return None
        try:
            return int(parts[1])
        except ValueError:
            return None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/tasks":
            self._send_json(404, {"error": "not found"})
            return
        tasks = list(self.server.tasks.values())
        status = parse_qs(parsed.query).get("status", [None])[0]
        if status is not None:
            tasks = [task for task in tasks if task["status"] == status]
        self._send_json(200, tasks)

    def do_POST(self):
        if self.path != "/tasks":
            self._send_json(404, {"error": "not found"})
            return
        data = self._read_json()
        if data is None:
            self._send_json(400, {"error": "malformed json"})
            return
        task_id = self.server.next_id
        self.server.next_id += 1
        task = {
            "id": task_id,
            "title": data.get("title", ""),
            "status": data.get("status", "todo"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.server.tasks[task_id] = task
        self._send_json(201, task)

    def do_PUT(self):
        task_id = self._task_id_from_path()
        if task_id is None or task_id not in self.server.tasks:
            self._send_json(404, {"error": "not found"})
            return
        data = self._read_json()
        if data is None:
            self._send_json(400, {"error": "malformed json"})
            return
        task = self.server.tasks[task_id]
        if "title" in data:
            task["title"] = data["title"]
        if "status" in data:
            task["status"] = data["status"]
        self._send_json(200, task)

    def do_DELETE(self):
        task_id = self._task_id_from_path()
        if task_id is None or task_id not in self.server.tasks:
            self._send_json(404, {"error": "not found"})
            return
        del self.server.tasks[task_id]
        self._send_json(204)


def create_app():
    server = ThreadingHTTPServer(("127.0.0.1", 0), TaskHandler)
    server.tasks = {}
    server.next_id = 1
    return server
