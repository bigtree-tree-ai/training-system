"""Minimal Streamable HTTP MCP client for COROS."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from training.coros.oauth import load_access_token


MCP_URL = os.getenv("COROS_MCP_URL", "https://mcpcn.coros.com/mcp")
PROTOCOL_VERSION = "2025-06-18"


class CorosMcpClient:
    """Read-only COROS MCP client using a bearer token from the environment."""

    def __init__(self, access_token: str | None = None, mcp_url: str = MCP_URL):
        self.access_token = access_token or os.getenv("COROS_MCP_ACCESS_TOKEN") or load_access_token()
        if not self.access_token:
            raise RuntimeError("COROS auth is missing. Run `python -m training.cli coros-login` first.")
        self.mcp_url = mcp_url
        self.session_id: str | None = None
        self.next_id = 1
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "training-system-coros-sync", "version": "1.0.0"},
            },
        )
        self._request("notifications/initialized", {}, expect_response=False)
        self._initialized = True

    def call_tool(self, name: str, arguments: dict | None = None):
        self.initialize()
        return self._request("tools/call", {"name": name, "arguments": arguments or {}})

    def _request(self, method: str, params: dict | None = None, expect_response: bool = True):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if expect_response:
            payload["id"] = self.next_id
            self.next_id += 1

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        req = urllib.request.Request(
            self.mcp_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                session_id = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
                if session_id:
                    self.session_id = session_id
                content_type = resp.headers.get("Content-Type") or ""
                if "text/event-stream" in content_type:
                    parsed = _read_sse_response(resp)
                else:
                    raw = resp.read().decode("utf-8")
                    parsed = json.loads(raw) if raw.strip() else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"COROS MCP HTTP {exc.code} for {method}: {detail}") from exc

        if not expect_response:
            return None
        if isinstance(parsed, dict) and parsed.get("error"):
            raise RuntimeError(f"COROS MCP error for {method}: {parsed['error']}")
        return parsed.get("result") if isinstance(parsed, dict) else parsed


def _read_sse_response(resp):
    data_lines = []
    while True:
        line = resp.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip("\r\n")
        if text == "":
            if data_lines:
                data = "\n".join(data_lines)
                if data and data != "[DONE]":
                    return json.loads(data)
                data_lines = []
            continue
        if text.startswith("data:"):
            data_lines.append(text[5:].strip())
    if data_lines:
        data = "\n".join(data_lines)
        return json.loads(data) if data and data != "[DONE]" else None
    return None
