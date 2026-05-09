import http.client
import importlib.util
import json
import threading
from contextlib import contextmanager
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rest_api_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
create_app = solution.create_app


@contextmanager
def running_server():
    server = create_app()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(server, method, path, body=None):
    conn = http.client.HTTPConnection(server.server_address[0], server.server_address[1])
    payload = None if body is None else json.dumps(body)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    data = response.read().decode()
    conn.close()
    return response.status, json.loads(data) if data else None


def test_get_empty_list():
    with running_server() as server:
        assert request(server, "GET", "/tasks") == (200, [])


def test_post_create_task():
    with running_server() as server:
        status, data = request(server, "POST", "/tasks", {"title": "write", "status": "todo"})
        assert status == 201
        assert data["id"] == 1
        assert data["title"] == "write"
        assert data["status"] == "todo"
        assert "created_at" in data


def test_put_existing_and_missing_task():
    with running_server() as server:
        request(server, "POST", "/tasks", {"title": "write", "status": "todo"})
        status, data = request(server, "PUT", "/tasks/1", {"status": "done"})
        assert status == 200
        assert data["status"] == "done"
        assert request(server, "PUT", "/tasks/999", {"status": "done"}) == (404, {"error": "not found"})


def test_delete_existing_and_missing_task():
    with running_server() as server:
        request(server, "POST", "/tasks", {"title": "write", "status": "todo"})
        assert request(server, "DELETE", "/tasks/1") == (204, None)
        assert request(server, "DELETE", "/tasks/1") == (404, {"error": "not found"})


def test_status_filter_and_repeated_get():
    with running_server() as server:
        request(server, "POST", "/tasks", {"title": "a", "status": "todo"})
        request(server, "POST", "/tasks", {"title": "b", "status": "done"})
        status, data = request(server, "GET", "/tasks?status=done")
        assert status == 200
        assert [task["title"] for task in data] == ["b"]
        assert request(server, "GET", "/tasks")[1] == request(server, "GET", "/tasks")[1]


def test_malformed_json_returns_400():
    with running_server() as server:
        conn = http.client.HTTPConnection(server.server_address[0], server.server_address[1])
        conn.request("POST", "/tasks", body="{bad", headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()
        assert response.status == 400
        assert data == {"error": "malformed json"}
