"""麦当劳 MCP Server 极简客户端（Streamable HTTP / JSON-RPC，仅标准库）。

官方接入信息：
  接入地址: https://mcp.mcd.cn
  传输协议: Streamable HTTP
  认证:     Authorization: Bearer <MCP_TOKEN>
限流:     每 Token 每分钟最多 600 次请求
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

DEFAULT_URL = "https://mcp.mcd.cn"


class MCPError(RuntimeError):
    """MCP 调用失败（网络错误 / JSON-RPC error / 限流 429 等）。"""


class McDonaldsMCP:
    """对麦当劳 MCP Server 的最小封装：initialize / tools/list / tools/call。"""

    def __init__(self, token: str, url: str = DEFAULT_URL, timeout: int = 30):
        if not token:
            raise ValueError("缺少 MCP Token，请从 https://open.mcd.cn/mcp 控制台申请")
        self.url = url
        self.token = token
        self.timeout = timeout
        self._session_id: str | None = None

    # ---------- 底层 RPC ----------
    def _rpc(self, method: str, params: dict | None = None) -> dict:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                self._session_id = resp.headers.get("Mcp-Session-Id") or self._session_id
                raw = resp.read().decode("utf-8", "replace")
                payload = self._parse_body(resp.headers.get("Content-Type", ""), raw)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429:
                raise MCPError("触发限流（429）：每 Token 每分钟最多 600 次请求，请稍后重试") from e
            raise MCPError(f"HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise MCPError(f"网络错误: {e.reason}") from e

        if "error" in payload:
            err = payload["error"]
            raise MCPError(f"MCP error {err.get('code')}: {err.get('message')}")
        return payload.get("result", {})

    @staticmethod
    def _parse_body(content_type: str, raw: str) -> dict:
        """服务端可能返回 application/json 或 text/event-stream(SSE)，两种都解析。"""
        if "text/event-stream" in content_type:
            for line in raw.splitlines():
                if line.startswith("data:"):
                    try:
                        return json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
            raise MCPError("SSE 响应中未找到有效 data 帧")
        return json.loads(raw)

    # ---------- 高层 API ----------
    def initialize(self) -> dict:
        return self._rpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "mcd-party-planner", "version": "1.0.0"},
        })

    def list_tools(self) -> list[dict]:
        result = self._rpc("tools/list")
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """调用工具并返回结构化内容（isError 时抛出 MCPError）。"""
        result = self._rpc("tools/call", {"name": name, "arguments": arguments or {}})
        if result.get("isError"):
            texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
            raise MCPError(f"工具 {name} 返回错误: {' '.join(texts)[:300]}")
        for c in result.get("content", []):
            if c.get("type") == "text":
                try:
                    return json.loads(c["text"])
                except json.JSONDecodeError:
                    return {"raw": c["text"]}
        return result

    # ---------- 本项目用到的便捷封装 ----------
    def nearby_stores(self, address: str) -> list[dict]:
        return self.call_tool("query-nearby-stores", {"address": address}).get("stores", [])

    def store_menu(self, store_code: str) -> list[dict]:
        return self.call_tool("query-meals", {"storeCode": store_code}).get("categories", [])

    def store_coupons(self, store_code: str) -> list[dict]:
        return self.call_tool("query-store-coupons", {"storeCode": store_code}).get("coupons", [])

    def nutrition_foods(self) -> list[dict]:
        return self.call_tool("list-nutrition-foods").get("foods", [])

    def calculate_price(self, store_code: str, items: list[dict], coupons: list[dict] | None = None) -> dict:
        args: dict = {"storeCode": store_code, "items": items}
        if coupons:
            args["coupons"] = coupons
        return self.call_tool("calculate-price", args)
