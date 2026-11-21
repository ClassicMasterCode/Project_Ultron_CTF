#!/usr/bin/env python3
"""
ULTRON Recovery Console - HTTP Service & Portal Backend
Implements authentication gateway, rate limiting, session management,
and API bridge to the ULTRON virtual command simulator.
"""
import sys
import os
import json
import time
import secrets
import struct
import hmac
import hashlib
import base64
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Tuple, Optional

# Import simulator engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ultron_sim import UltronSession, EXACT_FLAG

# Configuration
HOST = "0.0.0.0"
PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
FEEDBACK_DIR = os.path.join(BASE_DIR, "..", "private", "feedback")
if not os.path.exists(FEEDBACK_DIR):
    # Fallback to local feedback path
    FEEDBACK_DIR = os.path.join(BASE_DIR, "feedback")

# Challenge Credentials (default instance fixtures; can be overridden via env)
VALID_USERNAME = os.environ.get("ULTRON_OPERATOR_USER", "eward")
VALID_PASSWORD = os.environ.get("ULTRON_OPERATOR_PASS", "stark-disengage-recovery-441-alpha")
VALID_TOTP_SECRET = os.environ.get("ULTRON_TOTP_SECRET", "JBSWY3DPEHPK3PXP")

# In-memory and persistent disk session stores
sessions: Dict[str, UltronSession] = {}
SESSION_CACHE_DIR = os.path.join(tempfile.gettempdir(), "ultron_sessions")
os.makedirs(SESSION_CACHE_DIR, exist_ok=True)

def save_session(session: UltronSession):
    sessions[session.session_id] = session
    try:
        fpath = os.path.join(SESSION_CACHE_DIR, f"{session.session_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f)
    except Exception:
        pass

def get_session(session_id: Optional[str]) -> Optional[UltronSession]:
    if not session_id:
        return None
    if session_id in sessions:
        return sessions[session_id]
    try:
        fpath = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sess = UltronSession.from_dict(data, FEEDBACK_DIR)
            sessions[session_id] = sess
            return sess
    except Exception:
        pass
    return None

ip_attempts: Dict[str, list[float]] = {}
RATE_LIMIT_MAX = 6
RATE_LIMIT_WINDOW = 60 # seconds

def get_client_ip(headers, client_address) -> str:
    xff = headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    x_real_ip = headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    return client_address[0] if client_address else "127.0.0.1"

def verify_totp(secret_b32: str, code_to_check: str, interval: int = 30, skew_steps: int = 1) -> bool:
    """Verify TOTP code within clock skew window."""
    code_to_check = code_to_check.strip()
    if not code_to_check.isdigit() or len(code_to_check) != 6:
        return False

    cleaned = secret_b32.strip().replace(" ", "").upper()
    padding = len(cleaned) % 8
    if padding != 0:
        cleaned += "=" * (8 - padding)
    try:
        key = base64.b32decode(cleaned, casefold=True)
    except Exception:
        return False

    now = int(time.time())
    for offset in range(-skew_steps, skew_steps + 1):
        t = now + (offset * interval)
        counter = t // interval
        msg = struct.pack(">Q", counter)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        off = h[-1] & 0x0F
        code_int = struct.unpack(">I", h[off:off + 4])[0] & 0x7FFFFFFF
        expected = f"{code_int % 1_000_000:06d}"
        if hmac.compare_digest(expected, code_to_check):
            return True
    return False

def check_rate_limit(ip: str) -> bool:
    """Return True if within rate limit, False if exceeded."""
    now = time.time()
    if ip not in ip_attempts:
        ip_attempts[ip] = []
    # Purge old timestamps
    ip_attempts[ip] = [t for t in ip_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(ip_attempts[ip]) >= RATE_LIMIT_MAX:
        return False
    ip_attempts[ip].append(now)
    return True

class UltronHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-ID")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: str, content_type: str):
        if not os.path.exists(file_path):
            self.send_error(404, "File Not Found")
            return
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-ID")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "ultron-recovery-console",
                "isolation": "enforced",
                "timestamp": int(time.time())
            })
            return

        session_id = self.headers.get("X-Session-ID")
        session = get_session(session_id)

        if path == "/api/session":
            if not session:
                self._send_json(401, {"status": "unauthorized", "error": "Invalid or expired session"})
                return
            self._send_json(200, {
                "session_id": session.session_id,
                "username": session.username,
                "account_role": session.account_role,
                "effective_role": session.effective_role,
                "scope": session.scope,
                "milestones": session.milestones
            })
            return

        if path == "/api/feedback":
            if not session:
                self._send_json(401, {"status": "unauthorized", "error": "Invalid session"})
                return
            self._send_json(200, {
                "feedback": session.get_feedback()
            })
            return

        # Serve static frontend files
        if path == "/" or path == "/index.html":
            self._send_file(os.path.join(STATIC_DIR, "index.html"), "text/html")
        elif path == "/style.css":
            self._send_file(os.path.join(STATIC_DIR, "style.css"), "text/css")
        elif path == "/app.js":
            self._send_file(os.path.join(STATIC_DIR, "app.js"), "application/javascript")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        client_ip = get_client_ip(self.headers, self.client_address)

        # Read JSON body
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body = json.loads(post_data)
        except Exception:
            self._send_json(400, {"status": "error", "error": "Malformed JSON payload"})
            return

        if path == "/api/auth/login":
            # Rate limiting
            if not check_rate_limit(client_ip):
                self._send_json(429, {
                    "status": "rate_limited",
                    "error": "Authentication rate limit exceeded. Temporary cooldown active.",
                    "code": "RATE_LIMITED"
                })
                return

            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            totp = body.get("totp", "").strip()

            # Generic failure helper
            def auth_failed(reason_code):
                return self._send_json(401, {
                    "status": "error",
                    "error": "Authentication failed. Supplied operator factors were rejected.",
                    "code": reason_code
                })

            if username != VALID_USERNAME:
                auth_failed("INVALID_CREDENTIALS")
                return

            if password != VALID_PASSWORD:
                auth_failed("INVALID_CREDENTIALS")
                return

            if not verify_totp(VALID_TOTP_SECRET, totp):
                auth_failed("INVALID_SECOND_FACTOR")
                return

            # Success: create isolated session
            session_id = secrets.token_hex(16)
            session = UltronSession(session_id, username, FEEDBACK_DIR)
            save_session(session)

            self._send_json(200, {
                "status": "success",
                "session_id": session_id,
                "identity": f"Elias Ward ({username})",
                "account_role": "OPERATOR",
                "effective_role": "OPERATOR",
                "administration": "RESTRICTED",
                "message": "Authentication factors accepted. Operator workspace unlocked."
            })
            return

        # Endpoints requiring authenticated session
        session_id = self.headers.get("X-Session-ID") or body.get("session_id")
        session = get_session(session_id)
        if not session:
            self._send_json(401, {"status": "unauthorized", "error": "Session token missing or expired"})
            return

        if path == "/api/terminal":
            cmd = body.get("command", "").strip()
            result = session.execute_command(cmd)
            save_session(session)
            self._send_json(200, {
                "output": result,
                "effective_role": session.effective_role,
                "feedback": session.get_feedback(),
                "session_id": session.session_id
            })
            return

        if path == "/api/flag/validate":
            submitted_flag = body.get("flag", "").strip()
            if submitted_flag != EXACT_FLAG:
                self._send_json(200, {
                    "valid": False,
                    "message": "Incorrect flag value."
                })
                return

            # Check that participant achieved the prerequisite administrator state
            if session.effective_role != "ADMIN":
                self._send_json(200, {
                    "valid": False,
                    "message": "Flag submission rejected: session has not completed the sandbox administrator transition."
                })
                return

            if not session.milestones.get("final_artifact_accessed"):
                self._send_json(200, {
                    "valid": False,
                    "message": "Flag submission rejected: local file access event not verified in session."
                })
                return

            self._send_json(200, {
                "valid": True,
                "message": "Congratulations! ULTRON has been successfully disengaged. Flag validated.",
                "points": 500
            })
            return

        self.send_error(404, "Unknown API Endpoint")

def run(host=HOST, port=PORT):
    server = HTTPServer((host, port), UltronHandler)
    print(f"[ULTRON PORTAL] Service listening at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run(port=p)
