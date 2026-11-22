"""Offline API contract and safety tests: python -m unittest discover -s tests -p test_web_server.py."""
import base64
import http.client
import json
import threading
import time
import unittest

from web_server import ResearchServer, ResearchStore


def allowed_runner(question, memory, progress):
    progress("planning", "Planning the research")
    progress("evidence", "Checking the evidence")
    memory.add_turn(question, {"genes": ["PKD1"]}, "Allowed summary")
    return {"status": "completed", "answer": "Allowed summary", "decision": {"action": "allow"}}


class StoreTests(unittest.TestCase):
    def wait_for_result(self, store, owner, sid):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = store.get(owner, sid)
            if not result["busy"]:
                return result
            time.sleep(.01)
        self.fail("Research did not finish")

    def test_allowed_result_and_progress_commit_memory(self):
        store = ResearchStore(allowed_runner)
        sid = store.create("owner")["id"]
        store.start("owner", sid, "What is PKD1?")
        result = self.wait_for_result(store, "owner", sid)
        self.assertEqual(result["memory_turns"], 1)
        self.assertEqual(result["turns"][0]["status"], "completed")
        self.assertEqual([e["stage"] for e in result["turns"][0]["events"]], ["planning", "evidence"])

    def test_withheld_answer_is_removed_and_memory_not_committed(self):
        def withheld(question, memory, progress):
            memory.add_turn(question, {}, "Must not be remembered")
            return {"status": "completed", "answer": "Hidden draft", "decision": {"action": "withhold"}}
        store = ResearchStore(withheld)
        sid = store.create("owner")["id"]
        store.start("owner", sid, "Test question")
        result = self.wait_for_result(store, "owner", sid)
        self.assertEqual(result["memory_turns"], 0)
        self.assertEqual(result["turns"][0]["status"], "withheld")
        self.assertIsNone(result["turns"][0]["result"]["answer"])

    def test_exception_does_not_expose_details_or_commit_memory(self):
        def failure(question, memory, progress):
            memory.add_turn(question, {}, "Do not commit")
            raise RuntimeError("internal-sensitive-detail")
        store = ResearchStore(failure)
        sid = store.create("owner")["id"]
        with self.assertLogs("helix", level="ERROR"):
            store.start("owner", sid, "Test question")
            result = self.wait_for_result(store, "owner", sid)
        self.assertEqual(result["turns"][0]["status"], "error")
        self.assertNotIn("internal-sensitive-detail", json.dumps(result))
        self.assertEqual(result["memory_turns"], 0)

    def test_sessions_are_isolated_and_deleted(self):
        store = ResearchStore(allowed_runner)
        sid = store.create("alice")["id"]
        self.assertEqual(store.list("bob"), [])
        for operation in [lambda: store.get("bob", sid), lambda: store.delete("bob", sid), lambda: store.start("bob", sid, "Question")]:
            with self.assertRaises(KeyError):
                operation()
        store.delete("alice", sid)
        self.assertEqual(store.list("alice"), [])

    def test_concurrent_submissions_and_delete_are_rejected(self):
        release = threading.Event()
        def slow(question, memory, progress):
            release.wait(3)
            return allowed_runner(question, memory, progress)
        store = ResearchStore(slow)
        sid = store.create("owner")["id"]
        try:
            store.start("owner", sid, "Question")
            with self.assertRaises(ValueError):
                store.start("owner", sid, "Duplicate")
            with self.assertRaises(ValueError):
                store.delete("owner", sid)
        finally:
            release.set()
            self.wait_for_result(store, "owner", sid)

    def test_invalid_questions_rejected(self):
        store = ResearchStore(allowed_runner)
        sid = store.create("owner")["id"]
        for question in (None, {}, "   ", "a" * 4001):
            with self.assertRaises(ValueError):
                store.start("owner", sid, question)
        self.assertEqual(store.get("owner", sid)["turns"], [])


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ResearchServer(("127.0.0.1", 0), ResearchStore(allowed_runner))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request(method, path, json.dumps(body) if body is not None else None, headers or {})
        response = connection.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        connection.close()
        return result

    def test_static_assets_and_private_files(self):
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Evidence explorer", body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for path in ("/.env", "/../.env", "/web_server.py", "/unknown"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_cookie_isolation_and_research_api(self):
        status, headers, body = self.request("POST", "/api/sessions", {})
        self.assertEqual(status, 201)
        cookie = headers["Set-Cookie"].split(";")[0]
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        sid = json.loads(body)["id"]
        self.assertEqual(self.request("GET", f"/api/sessions/{sid}")[0], 404)
        auth = {"Cookie": cookie}
        self.assertEqual(self.request("POST", f"/api/sessions/{sid}/research", {"question": "What is PKD1?"}, auth)[0], 202)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = json.loads(self.request("GET", f"/api/sessions/{sid}", headers=auth)[2])
            if not result["busy"]:
                break
            time.sleep(.01)
        self.assertEqual(result["turns"][0]["result"]["answer"], "Allowed summary")

    def test_foreign_origin_and_host_rejected(self):
        self.assertEqual(self.request("POST", "/api/sessions", {}, {"Origin": "https://foreign.example"})[0], 403)
        self.assertEqual(self.request("GET", "/api/sessions", headers={"Host": "foreign.example"})[0], 403)

    def test_bad_payload_and_unknown_routes(self):
        self.assertEqual(self.request("POST", "/api/sessions", ["not an object"])[0], 400)
        self.assertEqual(self.request("GET", "/api/unknown")[0], 404)


class HostedHTTPTests(unittest.TestCase):
    def test_public_server_requires_https_origin_and_password(self):
        for kwargs in ({}, {"public_url": "http://demo.example", "demo_password": "test-password-long"},
                       {"public_url": "https://demo.example", "demo_password": "short"}):
            with self.assertRaises(ValueError):
                ResearchServer(("0.0.0.0", 0), **kwargs)

    def test_password_protects_frontend_and_api(self):
        password = "test-password-long"
        host = "demo.example"
        server = ResearchServer(
            ("127.0.0.1", 0), ResearchStore(allowed_runner),
            public_url=f"https://{host}", demo_password=password,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        def request(method, path, **headers):
            with_host = {"Host": host, **headers}
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            try:
                connection.request(method, path, b"{}" if method == "POST" else None, with_host)
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                connection.close()

        self.assertEqual(request("GET", "/healthz")[0], 200)
        for method, path in (("GET", "/"), ("GET", "/api/health"), ("POST", "/api/sessions")):
            status, headers, _ = request(method, path)
            self.assertEqual(status, 401)
            self.assertIn("Basic", headers["WWW-Authenticate"])
        self.assertEqual(request("GET", "/", Authorization="Basic wrong")[0], 401)

        token = base64.b64encode(f"helix:{password}".encode()).decode()
        auth = {"Authorization": f"Basic {token}"}
        self.assertEqual(request("GET", "/", **auth)[0], 200)
        self.assertEqual(request("GET", "/", **auth, Host="foreign.example")[0], 403)
        self.assertEqual(request("POST", "/api/sessions", **auth, Origin="https://foreign.example")[0], 403)
        self.assertEqual(request("POST", "/api/sessions", **auth)[0], 415)

        status, headers, body = request("POST", "/api/sessions", **auth, **{"Content-Type": "application/json"})
        self.assertEqual(status, 201)
        self.assertIn("; Secure", headers["Set-Cookie"])
        session_id = json.loads(body)["id"]
        research_path = f"/api/sessions/{session_id}/research"
        cookie = headers["Set-Cookie"].split(";")[0]
        self.assertEqual(request("POST", research_path, Cookie=cookie)[0], 401)


if __name__ == "__main__":
    unittest.main()
