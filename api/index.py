#!/usr/bin/env python3
"""
ULTRON Recovery Console — Vercel Serverless Function & HTTP API Gateway
Native Vercel Serverless Python entrypoint conforming to BaseHTTPRequestHandler.
Handles authentication gateway, persistent serverless sessions, rate limiting,
virtual terminal command execution, and disengagement flag verification.
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

# Ensure local api folder is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ultron_sim import UltronSession, EXACT_FLAG

# Challenge Credentials (default instance fixtures; can be overridden via env)
VALID_USERNAME = os.environ.get("ULTRON_OPERATOR_USER", "eward")
VALID_PASSWORD = os.environ.get("ULTRON_OPERATOR_PASS", "stark-disengage-recovery-441-alpha")
VALID_TOTP_SECRET = os.environ.get("ULTRON_TOTP_SECRET", "JBSWY3DPEHPK3PXP")

# Session persistence layer for Serverless execution
SESSION_CACHE_DIR = os.path.join(tempfile.gettempdir(), "ultron_sessions")
os.makedirs(SESSION_CACHE_DIR, exist_ok=True)

_sessions_cache: Dict[str, UltronSession] = {}
_ip_attempts: Dict[str, list[float]] = {}
RATE_LIMIT_MAX = 6
RATE_LIMIT_WINDOW = 60  # seconds

def save_session(session: UltronSession):
    """Save session to both in-memory cache and ephemeral disk store."""
    _sessions_cache[session.session_id] = session
    try:
        fpath = os.path.join(SESSION_CACHE_DIR, f"{session.session_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f)
    except Exception:
        pass

def get_session(session_id: Optional[str]) -> Optional[UltronSession]:
    """Retrieve session from in-memory cache or reload from ephemeral disk store."""
    if not session_id:
        return None
    if session_id in _sessions_cache:
        return _sessions_cache[session_id]
    try:
        fpath = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sess = UltronSession.from_dict(data)
            _sessions_cache[session_id] = sess
            return sess
    except Exception:
        pass
    return None

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
    if ip not in _ip_attempts:
        _ip_attempts[ip] = []
    # Purge old timestamps
    _ip_attempts[ip] = [t for t in _ip_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_ip_attempts[ip]) >= RATE_LIMIT_MAX:
        return False
    _ip_attempts[ip].append(now)
    return True

def extract_client_ip(headers, client_address) -> str:
    """Extract real client IP taking reverse proxy headers into account."""
    xff = headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    x_real_ip = headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    return client_address[0] if client_address else "127.0.0.1"


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless request handler.
    Vercel automatically directs HTTP invocations to this class.
    """

    def _send_json(self, status: int, data: dict, extra_headers: Optional[dict] = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # CORS & Security headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-ID, Authorization")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _get_normalized_path(self) -> str:
        """
        Normalize the requested API path across direct invocation,
        Vercel URL rewrites, and reverse proxy forwarded paths.
        """
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Check rewrite parameter: /api/:path* -> /api/index.py?path=:path*
        if "path" in qs and qs["path"]:
            sub = qs["path"][0].strip().lstrip("/")
            return f"/api/{sub}"

        # Check Vercel proxy headers
        fwd = self.headers.get("X-Forwarded-Uri") or self.headers.get("X-Matched-Path")
        if fwd:
            fwd_path = urlparse(fwd).path
            if fwd_path.startswith("/api/"):
                return fwd_path

        p = parsed.path
        if p == "/api/index.py" or p == "/api/index" or p == "/api":
            return "/api/health"
        return p

    def do_OPTIONS(self):
        """Respond to CORS preflight checks."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-ID, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        path = self._get_normalized_path()

        if path == "/api/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "ultron-recovery-console",
                "isolation": "enforced",
                "runtime": "vercel-serverless",
                "timestamp": int(time.time())
            })
            return

        session_id = self.headers.get("X-Session-ID")
        if not session_id:
            # Check query string for session_id fallback
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            session_id = qs.get("session_id", [None])[0]

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

        self._send_json(404, {"status": "error", "error": f"Endpoint not found: {path}"})

    def do_POST(self):
        path = self._get_normalized_path()
        client_ip = extract_client_ip(self.headers, self.client_address)

        # Parse JSON request payload
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body = json.loads(post_data)
        except Exception:
            self._send_json(400, {"status": "error", "error": "Malformed JSON payload"})
            return

        if path == "/api/auth/login":
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

            # Success: allocate persistent session
            session_id = secrets.token_hex(16)
            session = UltronSession(session_id, username)
            save_session(session)

            self._send_json(200, {
                "status": "success",
                "session_id": session_id,
                "identity": f"Elias Ward ({username})",
                "account_role": "OPERATOR",
                "effective_role": "OPERATOR",
                "administration": "RESTRICTED",
                "message": "Authentication factors accepted. Operator workspace unlocked."
            }, extra_headers={"Set-Cookie": f"ultron_session={session_id}; Path=/; SameSite=Lax"})
            return

        # Authenticated endpoints
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

            save_session(session)
            self._send_json(200, {
                "valid": True,
                "message": "Congratulations! ULTRON has been successfully disengaged. Flag validated.",
                "points": 500
            })
            return

        self._send_json(404, {"status": "error", "error": f"Unknown API Endpoint: {path}"})


# Alias handler for WSGI/framework compatibility if needed
app = handler

def run(port: int = 8080):
    """Run local development server."""
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"[ULTRON PORTAL - VERCEL COMPATIBLE] Service listening at http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(p)
