"""OAuth helpers for COROS MCP sync."""
from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import queue
import secrets
import socketserver
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

from training.config import PROJECT_ROOT


ISSUER = os.getenv("COROS_MCP_ISSUER", "https://mcpcn.coros.com")
SCOPE = "openid mcp.tools offline_access"
AUTH_FILE = Path(os.getenv("COROS_AUTH_FILE", str(PROJECT_ROOT / ".coros_auth.json")))


def load_access_token() -> str | None:
    data = _read_auth()
    if not data:
        return None
    expires_at = data.get("expires_at") or 0
    if data.get("access_token") and expires_at - time.time() > 120:
        return data["access_token"]
    if data.get("refresh_token") and data.get("client_id"):
        refreshed = refresh_token(data["client_id"], data["refresh_token"])
        data.update(refreshed)
        if "expires_in" in refreshed:
            data["expires_at"] = time.time() + int(refreshed["expires_in"])
        _write_auth(data)
        return data.get("access_token")
    return None


def login_with_browser() -> dict:
    result_queue = queue.Queue()
    _CallbackHandler.result_queue = result_queue
    with socketserver.TCPServer(("127.0.0.1", 0), _CallbackHandler) as httpd:
        port = httpd.server_address[1]
        redirect_uri = f"http://127.0.0.1:{port}/callback"
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        registration = register_client([redirect_uri])
        client_id = registration["client_id"]
        verifier = _b64url(secrets.token_bytes(32))
        challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
        state = _b64url(secrets.token_bytes(16))
        auth_url = f"{ISSUER}/oauth2/authorize?" + urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": SCOPE,
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        print(f"Open COROS authorization URL:\n{auth_url}")
        try:
            subprocess.run(["open", "-na", "Google Chrome", auth_url], check=False)
        except FileNotFoundError:
            pass

        callback = result_queue.get(timeout=300)
        httpd.shutdown()
        if callback.get("error"):
            raise RuntimeError(f"OAuth failed: {callback['error']}")
        if callback.get("state") != state:
            raise RuntimeError("OAuth state mismatch")

        token = _post_form(
            f"{ISSUER}/oauth2/token",
            {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "code": callback["code"],
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
        )
        token["client_id"] = client_id
        token["expires_at"] = time.time() + int(token.get("expires_in", 3600))
        _write_auth(token)
        return {"auth_file": str(AUTH_FILE), "has_refresh_token": bool(token.get("refresh_token"))}


def refresh_token(client_id: str, refresh: str) -> dict:
    return _post_form(
        f"{ISSUER}/oauth2/token",
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh,
        },
    )


def register_client(redirect_uris: list[str]) -> dict:
    return _post_json(
        f"{ISSUER}/connect/register",
        {
            "client_name": "Training System COROS MCP Sync",
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": SCOPE,
            "token_endpoint_auth_method": "none",
        },
    )


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    result_queue = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            self.result_queue.put({"code": params["code"][0], "state": params.get("state", [""])[0]})
            body = b"Authorization complete. You can close this tab."
            self.send_response(200)
        else:
            self.result_queue.put({"error": params.get("error", ["missing_code"])[0]})
            body = b"Authorization failed. You can close this tab."
            self.send_response(400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def _read_auth() -> dict:
    if not AUTH_FILE.exists():
        return {}
    return json.loads(AUTH_FILE.read_text(encoding="utf-8"))


def _write_auth(data: dict):
    AUTH_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(AUTH_FILE, 0o600)


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_form(url: str, payload: dict) -> dict:
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
