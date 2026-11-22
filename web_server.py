"""Helix frontend and JSON API. Run locally with python web_server.py.

Uses the standard library; existing research dependencies are loaded on demand.
Sessions are isolated by an HttpOnly browser cookie and live in server memory.
"""

from __future__ import annotations

import argparse
import base64
import copy
from hashlib import sha256
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import mimetypes
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlsplit

from core.session_memory import ResearchMemory

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
logger = logging.getLogger("helix")


def research_runner(question, memory, on_progress):
    # Loading the OpenAI/MCP stack can take time; keep the UI responsive.
    from agents.orchestrator import process_research_question
    return process_research_question(question, memory, on_progress=on_progress)


def configured():
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return True
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, separator, value = line.strip().removeprefix("export ").partition("=")
            if separator and key.strip() == "OPENAI_API_KEY":
                return bool(value.strip().strip("\"'"))
    return False


class ResearchStore:
    def __init__(self, runner=research_runner):
        self.runner = runner
        self.sessions = {}
        self.lock = threading.RLock()
        self.capacity = threading.BoundedSemaphore(2)

    def _owned(self, owner, session_id):
        session = self.sessions.get(session_id)
        if session is None or session["owner"] != owner:
            raise KeyError("Research session not found.")
        return session

    def _snapshot(self, session, full=True):
        fields = ("id", "title", "created_at", "updated_at", "busy")
        result = {key: session[key] for key in fields}
        result["turn_count"] = len(session["turns"])
        if full:
            result["turns"] = copy.deepcopy(session["turns"])
            result["memory_turns"] = len(session["memory"].get_history())
            result["explanation_style"] = session["memory"].explanation_style
        return result

    def create(self, owner):
        with self.lock:
            now = time.time()
            for key in list(self.sessions):
                session = self.sessions[key]
                if not session["busy"] and now - session["updated_at"] > 86400:
                    del self.sessions[key]
            if len(self.sessions) >= 100 or sum(s["owner"] == owner for s in self.sessions.values()) >= 20:
                raise ValueError("Session limit reached. Delete an older conversation first.")
            session = {
                "id": secrets.token_urlsafe(18), "owner": owner,
                "title": "New research", "created_at": now, "updated_at": now,
                "busy": False, "turns": [], "memory": ResearchMemory(max_turns=5),
            }
            self.sessions[session["id"]] = session
            return self._snapshot(session)

    def list(self, owner):
        with self.lock:
            return sorted(
                [self._snapshot(s, False) for s in self.sessions.values() if s["owner"] == owner],
                key=lambda s: s["updated_at"], reverse=True,
            )

    def get(self, owner, session_id):
        with self.lock:
            return self._snapshot(self._owned(owner, session_id))

    def delete(self, owner, session_id):
        with self.lock:
            session = self._owned(owner, session_id)
            if session["busy"]:
                raise ValueError("Wait for this research request to finish before deleting it.")
            del self.sessions[session_id]

    def start(self, owner, session_id, question):
        if not isinstance(question, str) or not question.strip() or len(question) > 4000:
            raise ValueError("Enter a research question between 1 and 4,000 characters.")
        with self.lock:
            session = self._owned(owner, session_id)
            if session["busy"]:
                raise ValueError("A question is already being researched in this conversation.")
            if len(session["turns"]) >= 50:
                raise ValueError("This conversation has reached 50 questions. Start a new conversation.")
            if not self.capacity.acquire(blocking=False):
                raise ValueError("The research engine is busy. Please try again shortly.")
            question = question.strip()
            turn = {
                "id": secrets.token_urlsafe(12), "question": question,
                "status": "running", "stage": "starting", "detail": "Preparing the research engine",
                "events": [], "started_at": time.time(), "result": None,
            }
            session["turns"].append(turn)
            session["busy"] = True
            session["updated_at"] = time.time()
            if len(session["turns"]) == 1:
                session["title"] = question[:90]
            threading.Thread(target=self._run, args=(session, turn), daemon=True).start()
            return self._snapshot(session)

    def _run(self, session, turn):
        def progress(stage, detail):
            with self.lock:
                turn.update(stage=stage, detail=detail)
                turn["events"].append({"stage": stage, "detail": detail, "at": time.time()})

        # Commit memory only after an allowed result, even if a runner fails midway.
        memory = copy.deepcopy(session["memory"])
        try:
            result = self.runner(turn["question"], memory, progress)
            allowed = result.get("status") == "completed" and (result.get("decision") or {}).get("action") == "allow"
            if not allowed:
                result["answer"] = None
            with self.lock:
                turn["result"] = result
                turn["status"] = "completed" if allowed else "withheld"
                if allowed:
                    session["memory"] = memory
        except Exception:
            logger.exception("Research request failed")
            with self.lock:
                turn["status"] = "error"
                turn["error"] = "Research could not be completed. Check your API configuration and connection, then retry."
        finally:
            with self.lock:
                turn["finished_at"] = time.time()
                session["updated_at"] = time.time()
                session["busy"] = False
            self.capacity.release()


class ResearchServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store=None, *, public_url=None, demo_password=None):
        self.store = store or ResearchStore()
        self.public_host = None
        self.public_origin = None
        self.demo_auth_digest = None
        if public_url:
            parsed = urlsplit(public_url)
            if (
                parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment
            ):
                raise ValueError("The public Helix URL must be an HTTPS origin.")
            if not demo_password or len(demo_password.strip()) < 16:
                raise ValueError("Set HELIX_DEMO_PASSWORD to a password of at least 16 characters.")
            self.public_host = parsed.netloc.lower()
            self.public_origin = f"https://{self.public_host}"
            token = base64.b64encode(f"helix:{demo_password}".encode("utf-8"))
            self.demo_auth_digest = sha256(token).digest()
        elif address[0] not in {"127.0.0.1", "localhost"}:
            raise ValueError("A public listener requires an HTTPS origin and demo password.")
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Avoid logging research text, cookies, or query strings.
        if args and str(args[1:2]) not in ("('200',)",):
            logger.debug(format, *args)

    def _send(self, status, data, content_type="application/json; charset=utf-8"):
        payload = json.dumps(data).encode() if content_type.startswith("application/json") else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if status == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="Helix capstone demo", charset="UTF-8"')
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if getattr(self, "new_owner", None):
            secure = "; Secure" if self.server.public_origin else ""
            self.send_header("Set-Cookie", f"helix_browser={self.new_owner}; Path=/; HttpOnly; SameSite=Strict{secure}")
        self.end_headers()
        self.wfile.write(payload)

    def _owner(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            pass
        owner = jar.get("helix_browser")
        if owner and len(owner.value) == 43 and all(c.isalnum() or c in "-_" for c in owner.value):
            return owner.value
        self.new_owner = secrets.token_urlsafe(32)
        return self.new_owner

    def _authenticated(self):
        scheme, _, token = self.headers.get("Authorization", "").partition(" ")
        return scheme.lower() == "basic" and secrets.compare_digest(
            sha256(token.strip().encode("utf-8")).digest(), self.server.demo_auth_digest
        )

    def _handle(self):
        try:
            host = self.headers.get("Host", "").lower()
            hosted = bool(self.server.public_origin)
            allowed_hosts = {self.server.public_host} if hosted else {
                f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"
            }
            if host not in allowed_hosts:
                self._send(403, {"error": "Use the configured Helix URL."})
                return
            origin = self.headers.get("Origin")
            expected_origin = self.server.public_origin or f"http://{host}"
            if origin and origin != expected_origin:
                self._send(403, {"error": "Cross-origin requests are not allowed."})
                return
            path = urlsplit(self.path).path
            if hosted:
                if path == "/healthz" and self.command == "GET":
                    self._send(200, {"status": "ready"})
                    return
                if not self._authenticated():
                    self._send(401, {"error": "Enter the demo username and password."})
                    return
            if not path.startswith("/api/"):
                if self.command != "GET":
                    self._send(405, {"error": "Method not allowed."})
                    return
                assets = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css", "/favicon.svg": "favicon.svg"}
                name = assets.get(path)
                if not name:
                    self._send(404, {"error": "Not found."})
                    return
                file = FRONTEND / name
                self._send(200, file.read_bytes(), mimetypes.guess_type(name)[0] or "application/octet-stream")
                return
            owner = self._owner()
            store = self.server.store
            body = {}
            if self.command == "POST":
                if hosted and self.headers.get_content_type() != "application/json":
                    self._send(415, {"error": "Send an application/json request."})
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 20000:
                    self._send(413, {"error": "Request is too large."})
                    return
                body = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object.")
            if path == "/api/health" and self.command == "GET":
                self._send(200, {"status": "ready", "configured": configured(), "storage": "session", "max_articles": 3})
            elif path == "/api/sessions" and self.command == "GET":
                self._send(200, {"sessions": store.list(owner)})
            elif path == "/api/sessions" and self.command == "POST":
                self._send(201, store.create(owner))
            else:
                parts = path.strip("/").split("/")
                if len(parts) in (3, 4) and parts[:2] == ["api", "sessions"]:
                    sid = parts[2]
                    if len(parts) == 3 and self.command == "GET":
                        self._send(200, store.get(owner, sid))
                    elif len(parts) == 3 and self.command == "DELETE":
                        store.delete(owner, sid)
                        self._send(200, {"deleted": True})
                    elif len(parts) == 4 and parts[3] == "research" and self.command == "POST":
                        self._send(202, store.start(owner, sid, body.get("question")))
                    else:
                        self._send(404, {"error": "Not found."})
                else:
                    self._send(404, {"error": "Not found."})
        except KeyError:
            self._send(404, {"error": "Research session not found. Start a new conversation."})
        except (ValueError, UnicodeDecodeError) as error:
            self._send(400, {"error": str(error) if not isinstance(error, json.JSONDecodeError) else "Invalid JSON."})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            logger.exception("API request failed")
            self._send(500, {"error": "The request could not be completed. Please try again."})

    do_GET = _handle
    do_POST = _handle
    do_DELETE = _handle


def main():
    parser = argparse.ArgumentParser(description="Helix gene–disease research workspace")
    parser.add_argument("--port", type=int, help="Override the default listening port")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    public_url = os.environ.get("RENDER_EXTERNAL_URL")
    if os.environ.get("RENDER") == "true" and not public_url:
        parser.error("Render must provide RENDER_EXTERNAL_URL for the hosted demo.")
    if public_url and not os.environ.get("OPENAI_API_KEY", "").strip():
        parser.error("Set OPENAI_API_KEY in the hosting dashboard.")
    try:
        default_port = int(os.environ.get("PORT", "10000")) if public_url else 8000
        port = args.port if args.port is not None else default_port
        server = ResearchServer(
            ("0.0.0.0" if public_url else "127.0.0.1", port),
            public_url=public_url,
            demo_password=os.environ.get("HELIX_DEMO_PASSWORD"),
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"Helix is running at {server.public_origin or f'http://127.0.0.1:{server.server_port}'}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
